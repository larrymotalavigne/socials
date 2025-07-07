"""
Telegram Bot for Content Review and Approval.

This module provides a Telegram bot interface for reviewing and approving
AI-generated content before publishing to Instagram.
"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
from pathlib import Path
from enum import Enum

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    InputMediaPhoto
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

from config import get_config
from utils.logger import get_logger, log_execution_time
from utils.exceptions import (
    TelegramError,
    ValidationError,
    handle_exception
)


class ApprovalStatus(Enum):
    """Content approval status."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"


class ContentReview:
    """Represents a content review request."""
    
    def __init__(
        self,
        review_id: str,
        content_type: str,
        image_path: Optional[str] = None,
        caption: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        callback: Optional[Callable] = None
    ):
        self.review_id = review_id
        self.content_type = content_type
        self.image_path = image_path
        self.caption = caption
        self.metadata = metadata or {}
        self.callback = callback
        self.status = ApprovalStatus.PENDING
        self.created_at = datetime.now()
        self.reviewed_at = None
        self.reviewer_id = None
        self.reviewer_username = None
        self.comments = []
        self.modifications = {}


class TelegramReviewBot:
    """Telegram bot for content review and approval."""
    
    def __init__(self):
        """Initialize the Telegram bot."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.application = None
        self.reviews: Dict[str, ContentReview] = {}
        self.review_history: List[Dict[str, Any]] = []
        self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize the Telegram bot application."""
        try:
            if not self.config.telegram.bot_token:
                raise TelegramError("Telegram bot token is required")
            
            # Create application
            self.application = Application.builder().token(
                self.config.telegram.bot_token
            ).build()
            
            # Add handlers
            self._add_handlers()
            
            self.logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize Telegram bot: {str(e)}")
            raise TelegramError(
                "Failed to initialize Telegram bot",
                original_exception=e
            )
    
    def _add_handlers(self):
        """Add command and callback handlers to the bot."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self._start_command))
        self.application.add_handler(CommandHandler("help", self._help_command))
        self.application.add_handler(CommandHandler("status", self._status_command))
        self.application.add_handler(CommandHandler("history", self._history_command))
        self.application.add_handler(CommandHandler("pending", self._pending_command))
        
        # Callback query handlers for inline keyboards
        self.application.add_handler(CallbackQueryHandler(
            self._handle_approval_callback,
            pattern=r"^(approve|reject|modify)_.*"
        ))
        
        self.application.add_handler(CallbackQueryHandler(
            self._handle_modification_callback,
            pattern=r"^mod_.*"
        ))
        
        # Message handlers for text modifications
        self.application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            self._handle_text_modification
        ))
    
    async def _start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command."""
        user = update.effective_user
        
        welcome_message = f"""
🤖 Welcome to AI Instagram Publisher Review Bot!

Hello {user.first_name}! I'm here to help you review and approve AI-generated content before it gets published to Instagram.

Available commands:
/help - Show this help message
/status - Show bot status and statistics
/pending - Show pending reviews
/history - Show recent review history

I'll send you content for review automatically when new content is generated.
        """
        
        await update.message.reply_text(welcome_message.strip())
        
        self.logger.info(
            f"User {user.username} ({user.id}) started the bot",
            extra={'extra_data': {
                'user_id': user.id,
                'username': user.username,
                'first_name': user.first_name
            }}
        )
    
    async def _help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command."""
        help_message = """
🔍 **Content Review Bot Help**

**Commands:**
• `/start` - Initialize the bot
• `/help` - Show this help message
• `/status` - Show bot status and statistics
• `/pending` - Show pending reviews
• `/history` - Show recent review history

**Review Process:**
1. I'll send you generated content (image + caption)
2. Use the inline buttons to:
   • ✅ **Approve** - Publish as-is
   • ❌ **Reject** - Don't publish
   • ✏️ **Modify** - Edit before publishing

**Modification Options:**
• Edit caption text
• Add/remove hashtags
• Change posting schedule

**Tips:**
• Reviews expire after 24 hours
• You can review multiple items simultaneously
• All actions are logged for audit purposes
        """
        
        await update.message.reply_text(help_message.strip(), parse_mode='Markdown')
    
    async def _status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /status command."""
        stats = self._get_review_statistics()
        
        status_message = f"""
📊 **Review Bot Status**

**Current Reviews:**
• Pending: {stats['pending_reviews']}
• Total Active: {stats['total_reviews']}

**Statistics:**
• Total Processed: {stats['total_processed']}
• Approved: {stats['approved_count']} ({stats['approval_rate']:.1f}%)
• Rejected: {stats['rejected_count']} ({stats['rejection_rate']:.1f}%)
• Modified: {stats['modified_count']} ({stats['modification_rate']:.1f}%)

**Performance:**
• Average Review Time: {stats['avg_review_time']} minutes
• Reviews Today: {stats['reviews_today']}

Bot is {'🟢 Online' if self.application else '🔴 Offline'}
        """
        
        await update.message.reply_text(status_message.strip(), parse_mode='Markdown')
    
    async def _pending_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /pending command."""
        pending_reviews = [
            review for review in self.reviews.values()
            if review.status == ApprovalStatus.PENDING
        ]
        
        if not pending_reviews:
            await update.message.reply_text("✅ No pending reviews!")
            return
        
        message = f"📋 **Pending Reviews ({len(pending_reviews)}):**\n\n"
        
        for review in pending_reviews[:10]:  # Show max 10
            age = datetime.now() - review.created_at
            age_str = f"{age.seconds // 3600}h {(age.seconds % 3600) // 60}m"
            
            message += f"• `{review.review_id[:8]}` - {review.content_type} ({age_str} ago)\n"
        
        if len(pending_reviews) > 10:
            message += f"\n... and {len(pending_reviews) - 10} more"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /history command."""
        recent_history = self.review_history[-10:]  # Last 10 reviews
        
        if not recent_history:
            await update.message.reply_text("📝 No review history yet.")
            return
        
        message = "📚 **Recent Review History:**\n\n"
        
        for entry in reversed(recent_history):
            status_emoji = {
                'approved': '✅',
                'rejected': '❌',
                'modified': '✏️'
            }.get(entry['status'], '❓')
            
            reviewed_at = datetime.fromisoformat(entry['reviewed_at'])
            time_str = reviewed_at.strftime("%m/%d %H:%M")
            
            message += f"{status_emoji} `{entry['review_id'][:8]}` - {entry['content_type']} ({time_str})\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
    
    async def _handle_approval_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle approval/rejection/modification callbacks."""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        action, review_id = query.data.split('_', 1)
        
        if review_id not in self.reviews:
            await query.edit_message_text("❌ Review not found or already processed.")
            return
        
        review = self.reviews[review_id]
        user = update.effective_user
        
        if action == "approve":
            await self._approve_content(query, review, user)
        elif action == "reject":
            await self._reject_content(query, review, user)
        elif action == "modify":
            await self._start_modification(query, review, user)
    
    async def _approve_content(self, query, review: ContentReview, user):
        """Approve content for publishing."""
        review.status = ApprovalStatus.APPROVED
        review.reviewed_at = datetime.now()
        review.reviewer_id = user.id
        review.reviewer_username = user.username
        
        # Execute callback if provided
        if review.callback:
            try:
                await review.callback(review, ApprovalStatus.APPROVED)
            except Exception as e:
                self.logger.error(f"Callback execution failed: {str(e)}")
        
        # Update message
        await query.edit_message_text(
            f"✅ **Content Approved**\n\n"
            f"Review ID: `{review.review_id}`\n"
            f"Approved by: @{user.username}\n"
            f"Time: {review.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Content will be published to Instagram.",
            parse_mode='Markdown'
        )
        
        # Add to history
        self._add_to_history(review)
        
        self.logger.info(
            f"Content approved: {review.review_id}",
            extra={'extra_data': {
                'review_id': review.review_id,
                'reviewer_id': user.id,
                'reviewer_username': user.username
            }}
        )
    
    async def _reject_content(self, query, review: ContentReview, user):
        """Reject content."""
        review.status = ApprovalStatus.REJECTED
        review.reviewed_at = datetime.now()
        review.reviewer_id = user.id
        review.reviewer_username = user.username
        
        # Execute callback if provided
        if review.callback:
            try:
                await review.callback(review, ApprovalStatus.REJECTED)
            except Exception as e:
                self.logger.error(f"Callback execution failed: {str(e)}")
        
        # Update message
        await query.edit_message_text(
            f"❌ **Content Rejected**\n\n"
            f"Review ID: `{review.review_id}`\n"
            f"Rejected by: @{user.username}\n"
            f"Time: {review.reviewed_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            f"Content will not be published.",
            parse_mode='Markdown'
        )
        
        # Add to history
        self._add_to_history(review)
        
        self.logger.info(
            f"Content rejected: {review.review_id}",
            extra={'extra_data': {
                'review_id': review.review_id,
                'reviewer_id': user.id,
                'reviewer_username': user.username
            }}
        )
    
    async def _start_modification(self, query, review: ContentReview, user):
        """Start content modification process."""
        keyboard = [
            [
                InlineKeyboardButton("✏️ Edit Caption", callback_data=f"mod_caption_{review.review_id}"),
                InlineKeyboardButton("🏷️ Edit Hashtags", callback_data=f"mod_hashtags_{review.review_id}")
            ],
            [
                InlineKeyboardButton("⏰ Schedule Later", callback_data=f"mod_schedule_{review.review_id}"),
                InlineKeyboardButton("🔙 Back to Review", callback_data=f"back_{review.review_id}")
            ]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            f"✏️ **Modify Content**\n\n"
            f"Review ID: `{review.review_id}`\n\n"
            f"What would you like to modify?",
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    
    async def _handle_modification_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle modification-specific callbacks."""
        query = update.callback_query
        await query.answer()
        
        # Parse callback data
        parts = query.data.split('_')
        action = parts[1]
        review_id = '_'.join(parts[2:])
        
        if review_id not in self.reviews:
            await query.edit_message_text("❌ Review not found.")
            return
        
        review = self.reviews[review_id]
        
        if action == "caption":
            await self._modify_caption(query, review)
        elif action == "hashtags":
            await self._modify_hashtags(query, review)
        elif action == "schedule":
            await self._modify_schedule(query, review)
    
    async def _modify_caption(self, query, review: ContentReview):
        """Start caption modification."""
        await query.edit_message_text(
            f"✏️ **Edit Caption**\n\n"
            f"Current caption:\n"
            f"```\n{review.caption}\n```\n\n"
            f"Please send me the new caption text:",
            parse_mode='Markdown'
        )
        
        # Store modification context
        review.metadata['modification_type'] = 'caption'
        review.metadata['modification_chat_id'] = query.message.chat_id
        review.metadata['modification_message_id'] = query.message.message_id
    
    async def _handle_text_modification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text modifications sent by user."""
        # Find review waiting for modification
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        for review in self.reviews.values():
            if (review.metadata.get('modification_chat_id') == chat_id and
                review.metadata.get('modification_type')):
                
                modification_type = review.metadata['modification_type']
                new_text = update.message.text
                
                if modification_type == 'caption':
                    review.modifications['original_caption'] = review.caption
                    review.caption = new_text
                    review.status = ApprovalStatus.MODIFIED
                    review.reviewed_at = datetime.now()
                    review.reviewer_id = user_id
                    review.reviewer_username = update.effective_user.username
                    
                    # Execute callback with modified content
                    if review.callback:
                        try:
                            await review.callback(review, ApprovalStatus.MODIFIED)
                        except Exception as e:
                            self.logger.error(f"Callback execution failed: {str(e)}")
                    
                    await update.message.reply_text(
                        f"✅ **Caption Updated**\n\n"
                        f"Review ID: `{review.review_id}`\n"
                        f"Modified by: @{update.effective_user.username}\n\n"
                        f"New caption:\n```\n{new_text}\n```\n\n"
                        f"Content will be published with the modified caption.",
                        parse_mode='Markdown'
                    )
                    
                    # Add to history
                    self._add_to_history(review)
                    
                    # Clear modification context
                    review.metadata.pop('modification_type', None)
                    review.metadata.pop('modification_chat_id', None)
                    review.metadata.pop('modification_message_id', None)
                    
                    break
    
    def _add_to_history(self, review: ContentReview):
        """Add review to history."""
        self.review_history.append({
            'review_id': review.review_id,
            'content_type': review.content_type,
            'status': review.status.value,
            'created_at': review.created_at.isoformat(),
            'reviewed_at': review.reviewed_at.isoformat() if review.reviewed_at else None,
            'reviewer_id': review.reviewer_id,
            'reviewer_username': review.reviewer_username,
            'modifications': review.modifications
        })
        
        # Keep only last 1000 entries
        if len(self.review_history) > 1000:
            self.review_history = self.review_history[-1000:]
    
    def _get_review_statistics(self) -> Dict[str, Any]:
        """Get review statistics."""
        total_reviews = len(self.reviews)
        pending_reviews = len([r for r in self.reviews.values() if r.status == ApprovalStatus.PENDING])
        
        history_stats = {}
        if self.review_history:
            approved = len([h for h in self.review_history if h['status'] == 'approved'])
            rejected = len([h for h in self.review_history if h['status'] == 'rejected'])
            modified = len([h for h in self.review_history if h['status'] == 'modified'])
            total_processed = len(self.review_history)
            
            history_stats = {
                'approved_count': approved,
                'rejected_count': rejected,
                'modified_count': modified,
                'total_processed': total_processed,
                'approval_rate': (approved / total_processed * 100) if total_processed > 0 else 0,
                'rejection_rate': (rejected / total_processed * 100) if total_processed > 0 else 0,
                'modification_rate': (modified / total_processed * 100) if total_processed > 0 else 0,
            }
            
            # Calculate average review time
            review_times = []
            for h in self.review_history:
                if h['reviewed_at']:
                    created = datetime.fromisoformat(h['created_at'])
                    reviewed = datetime.fromisoformat(h['reviewed_at'])
                    review_times.append((reviewed - created).total_seconds() / 60)
            
            avg_review_time = sum(review_times) / len(review_times) if review_times else 0
            history_stats['avg_review_time'] = f"{avg_review_time:.1f}"
            
            # Reviews today
            today = datetime.now().date()
            reviews_today = len([
                h for h in self.review_history
                if h['reviewed_at'] and datetime.fromisoformat(h['reviewed_at']).date() == today
            ])
            history_stats['reviews_today'] = reviews_today
        else:
            history_stats = {
                'approved_count': 0,
                'rejected_count': 0,
                'modified_count': 0,
                'total_processed': 0,
                'approval_rate': 0,
                'rejection_rate': 0,
                'modification_rate': 0,
                'avg_review_time': '0.0',
                'reviews_today': 0
            }
        
        return {
            'total_reviews': total_reviews,
            'pending_reviews': pending_reviews,
            **history_stats
        }
    
    @log_execution_time
    async def submit_for_review(
        self,
        content_type: str,
        image_path: Optional[str] = None,
        caption: Optional[str] = None,
        metadata: Dict[str, Any] = None,
        callback: Optional[Callable] = None
    ) -> str:
        """Submit content for review.
        
        Args:
            content_type: Type of content being reviewed
            image_path: Path to image file (if applicable)
            caption: Caption text (if applicable)
            metadata: Additional metadata
            callback: Callback function to execute after review
            
        Returns:
            Review ID
        """
        try:
            review_id = f"review_{uuid.uuid4().hex[:8]}"
            
            # Create review
            review = ContentReview(
                review_id=review_id,
                content_type=content_type,
                image_path=image_path,
                caption=caption,
                metadata=metadata or {},
                callback=callback
            )
            
            self.reviews[review_id] = review
            
            # Send to Telegram for review
            await self._send_review_message(review)
            
            self.logger.info(
                f"Content submitted for review: {review_id}",
                extra={'extra_data': {
                    'review_id': review_id,
                    'content_type': content_type,
                    'has_image': bool(image_path),
                    'has_caption': bool(caption)
                }}
            )
            
            return review_id
            
        except Exception as e:
            self.logger.error(f"Failed to submit content for review: {str(e)}")
            handle_exception(e, {"component": "telegram_review"})
            raise TelegramError(
                f"Failed to submit content for review: {str(e)}",
                original_exception=e
            )
    
    async def _send_review_message(self, review: ContentReview):
        """Send review message to Telegram."""
        if not self.config.telegram.chat_id:
            raise TelegramError("Telegram chat ID not configured")
        
        # Create inline keyboard
        keyboard = [
            [
                InlineKeyboardButton("✅ Approve", callback_data=f"approve_{review.review_id}"),
                InlineKeyboardButton("❌ Reject", callback_data=f"reject_{review.review_id}"),
                InlineKeyboardButton("✏️ Modify", callback_data=f"modify_{review.review_id}")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        # Prepare message text
        message_text = f"""
🔍 **Content Review Request**

**Review ID:** `{review.review_id}`
**Type:** {review.content_type}
**Created:** {review.created_at.strftime('%Y-%m-%d %H:%M:%S')}

**Caption:**
```
{review.caption or 'No caption'}
```

Please review and choose an action:
        """.strip()
        
        try:
            if review.image_path and Path(review.image_path).exists():
                # Send image with caption
                with open(review.image_path, 'rb') as image_file:
                    await self.application.bot.send_photo(
                        chat_id=self.config.telegram.chat_id,
                        photo=image_file,
                        caption=message_text,
                        reply_markup=reply_markup,
                        parse_mode='Markdown'
                    )
            else:
                # Send text message only
                await self.application.bot.send_message(
                    chat_id=self.config.telegram.chat_id,
                    text=message_text,
                    reply_markup=reply_markup,
                    parse_mode='Markdown'
                )
                
        except Exception as e:
            self.logger.error(f"Failed to send review message: {str(e)}")
            raise TelegramError(f"Failed to send review message: {str(e)}")
    
    async def start_bot(self):
        """Start the Telegram bot."""
        try:
            await self.application.initialize()
            await self.application.start()
            await self.application.updater.start_polling()
            
            self.logger.info("Telegram bot started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start Telegram bot: {str(e)}")
            raise TelegramError(
                "Failed to start Telegram bot",
                original_exception=e
            )
    
    async def stop_bot(self):
        """Stop the Telegram bot."""
        try:
            if self.application:
                await self.application.updater.stop()
                await self.application.stop()
                await self.application.shutdown()
            
            self.logger.info("Telegram bot stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to stop Telegram bot: {str(e)}")
            raise TelegramError(
                "Failed to stop Telegram bot",
                original_exception=e
            )


# Global bot instance
_telegram_bot = None


def get_telegram_bot() -> TelegramReviewBot:
    """Get or create the global Telegram bot instance."""
    global _telegram_bot
    if _telegram_bot is None:
        _telegram_bot = TelegramReviewBot()
    return _telegram_bot


# Convenience function for submitting content for review
async def submit_content_for_review(
    content_type: str,
    image_path: Optional[str] = None,
    caption: Optional[str] = None,
    metadata: Dict[str, Any] = None,
    callback: Optional[Callable] = None
) -> str:
    """Submit content for Telegram review.
    
    Args:
        content_type: Type of content being reviewed
        image_path: Path to image file
        caption: Caption text
        metadata: Additional metadata
        callback: Callback function after review
        
    Returns:
        Review ID
    """
    bot = get_telegram_bot()
    return await bot.submit_for_review(
        content_type=content_type,
        image_path=image_path,
        caption=caption,
        metadata=metadata,
        callback=callback
    )
