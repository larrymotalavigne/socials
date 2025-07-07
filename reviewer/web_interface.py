"""
Web-based Content Review Interface.

This module provides a Flask web application for reviewing and approving
AI-generated content as an alternative to the Telegram bot interface.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path
from functools import wraps

from flask import (
    Flask, 
    render_template_string, 
    request, 
    jsonify, 
    redirect, 
    url_for,
    session,
    flash,
    send_file
)

from config import get_config
from utils.logger import get_logger, log_execution_time
from utils.exceptions import (
    ValidationError,
    handle_exception
)
from reviewer.telegram_bot import (
    ContentReview,
    ApprovalStatus,
    get_telegram_bot
)


class WebReviewInterface:
    """Web-based content review interface."""
    
    def __init__(self):
        """Initialize the web interface."""
        self.logger = get_logger(__name__)
        self.config = get_config()
        self.app = Flask(__name__)
        self.app.secret_key = 'ai-instagram-publisher-review-key'  # In production, use a secure random key
        self.telegram_bot = get_telegram_bot()
        self._setup_routes()
    
    def _setup_routes(self):
        """Set up Flask routes."""
        
        @self.app.route('/')
        def index():
            """Main dashboard."""
            return self._render_dashboard()
        
        @self.app.route('/login', methods=['GET', 'POST'])
        def login():
            """Simple login page."""
            if request.method == 'POST':
                # Simple authentication - in production, use proper auth
                username = request.form.get('username')
                password = request.form.get('password')
                
                # Basic auth check (in production, use proper authentication)
                if username == 'admin' and password == 'review123':
                    session['authenticated'] = True
                    session['username'] = username
                    flash('Logged in successfully!', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Invalid credentials!', 'error')
            
            return self._render_login()
        
        @self.app.route('/logout')
        def logout():
            """Logout."""
            session.clear()
            flash('Logged out successfully!', 'info')
            return redirect(url_for('login'))
        
        @self.app.route('/reviews')
        @self._require_auth
        def reviews():
            """List all reviews."""
            return self._render_reviews()
        
        @self.app.route('/review/<review_id>')
        @self._require_auth
        def review_detail(review_id):
            """Show detailed review page."""
            return self._render_review_detail(review_id)
        
        @self.app.route('/api/approve/<review_id>', methods=['POST'])
        @self._require_auth
        def approve_review(review_id):
            """Approve a review via API."""
            return self._handle_approval(review_id, ApprovalStatus.APPROVED)
        
        @self.app.route('/api/reject/<review_id>', methods=['POST'])
        @self._require_auth
        def reject_review(review_id):
            """Reject a review via API."""
            return self._handle_approval(review_id, ApprovalStatus.REJECTED)
        
        @self.app.route('/api/modify/<review_id>', methods=['POST'])
        @self._require_auth
        def modify_review(review_id):
            """Modify a review via API."""
            return self._handle_modification(review_id)
        
        @self.app.route('/api/stats')
        @self._require_auth
        def get_stats():
            """Get review statistics."""
            stats = self.telegram_bot._get_review_statistics()
            return jsonify(stats)
        
        @self.app.route('/image/<review_id>')
        @self._require_auth
        def serve_image(review_id):
            """Serve review image."""
            if review_id in self.telegram_bot.reviews:
                review = self.telegram_bot.reviews[review_id]
                if review.image_path and Path(review.image_path).exists():
                    return send_file(review.image_path)
            return "Image not found", 404
    
    def _require_auth(self, f):
        """Decorator to require authentication."""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('authenticated'):
                return redirect(url_for('login'))
            return f(*args, **kwargs)
        return decorated_function
    
    def _render_login(self):
        """Render login page."""
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Instagram Publisher - Review Login</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .container { max-width: 400px; margin: 100px auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                .form-group { margin-bottom: 20px; }
                label { display: block; margin-bottom: 5px; font-weight: bold; }
                input[type="text"], input[type="password"] { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
                .btn { background: #007bff; color: white; padding: 12px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%; font-size: 16px; }
                .btn:hover { background: #0056b3; }
                .alert { padding: 10px; margin-bottom: 20px; border-radius: 4px; }
                .alert-error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
                .alert-success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
                .alert-info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
                h1 { text-align: center; color: #333; margin-bottom: 30px; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖📸 Review Login</h1>
                
                {% with messages = get_flashed_messages(with_categories=true) %}
                    {% if messages %}
                        {% for category, message in messages %}
                            <div class="alert alert-{{ category }}">{{ message }}</div>
                        {% endfor %}
                    {% endif %}
                {% endwith %}
                
                <form method="POST">
                    <div class="form-group">
                        <label for="username">Username:</label>
                        <input type="text" id="username" name="username" required>
                    </div>
                    <div class="form-group">
                        <label for="password">Password:</label>
                        <input type="password" id="password" name="password" required>
                    </div>
                    <button type="submit" class="btn">Login</button>
                </form>
                
                <p style="text-align: center; margin-top: 20px; color: #666; font-size: 14px;">
                    Demo credentials: admin / review123
                </p>
            </div>
        </body>
        </html>
        """
        return render_template_string(template)
    
    def _render_dashboard(self):
        """Render main dashboard."""
        if not session.get('authenticated'):
            return redirect(url_for('login'))
        
        stats = self.telegram_bot._get_review_statistics()
        pending_reviews = [
            review for review in self.telegram_bot.reviews.values()
            if review.status == ApprovalStatus.PENDING
        ]
        
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AI Instagram Publisher - Review Dashboard</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header h1 { margin: 0; color: #333; }
                .header .user-info { float: right; }
                .header .user-info a { color: #007bff; text-decoration: none; margin-left: 15px; }
                .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 30px; }
                .stat-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); text-align: center; }
                .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
                .stat-label { color: #666; margin-top: 5px; }
                .pending-reviews { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .review-item { border: 1px solid #eee; border-radius: 4px; padding: 15px; margin-bottom: 10px; }
                .review-item:hover { background: #f9f9f9; }
                .review-id { font-family: monospace; color: #666; font-size: 0.9em; }
                .review-type { font-weight: bold; color: #333; }
                .review-time { color: #999; font-size: 0.9em; }
                .btn { background: #007bff; color: white; padding: 8px 16px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin-right: 10px; }
                .btn:hover { background: #0056b3; }
                .btn-success { background: #28a745; }
                .btn-danger { background: #dc3545; }
                .btn-warning { background: #ffc107; color: #212529; }
                .clearfix::after { content: ""; display: table; clear: both; }
            </style>
        </head>
        <body>
            <div class="header clearfix">
                <h1>🤖📸 AI Instagram Publisher - Review Dashboard</h1>
                <div class="user-info">
                    Welcome, {{ session.username }}!
                    <a href="{{ url_for('reviews') }}">All Reviews</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                </div>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{{ stats.pending_reviews }}</div>
                    <div class="stat-label">Pending Reviews</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.total_processed }}</div>
                    <div class="stat-label">Total Processed</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ "%.1f"|format(stats.approval_rate) }}%</div>
                    <div class="stat-label">Approval Rate</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ stats.reviews_today }}</div>
                    <div class="stat-label">Reviews Today</div>
                </div>
            </div>
            
            <div class="pending-reviews">
                <h2>Pending Reviews ({{ pending_reviews|length }})</h2>
                
                {% if pending_reviews %}
                    {% for review in pending_reviews %}
                        <div class="review-item">
                            <div class="review-id">ID: {{ review.review_id }}</div>
                            <div class="review-type">{{ review.content_type }}</div>
                            <div class="review-time">Created: {{ review.created_at.strftime('%Y-%m-%d %H:%M:%S') }}</div>
                            <div style="margin-top: 10px;">
                                <a href="{{ url_for('review_detail', review_id=review.review_id) }}" class="btn">Review</a>
                            </div>
                        </div>
                    {% endfor %}
                {% else %}
                    <p>No pending reviews! 🎉</p>
                {% endif %}
            </div>
            
            <script>
                // Auto-refresh every 30 seconds
                setTimeout(function() {
                    location.reload();
                }, 30000);
            </script>
        </body>
        </html>
        """
        return render_template_string(
            template, 
            stats=stats, 
            pending_reviews=pending_reviews,
            session=session
        )
    
    def _render_reviews(self):
        """Render all reviews page."""
        all_reviews = list(self.telegram_bot.reviews.values())
        all_reviews.sort(key=lambda x: x.created_at, reverse=True)
        
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>All Reviews - AI Instagram Publisher</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header h1 { margin: 0; color: #333; }
                .header .nav { float: right; }
                .header .nav a { color: #007bff; text-decoration: none; margin-left: 15px; }
                .reviews-container { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .review-item { border: 1px solid #eee; border-radius: 4px; padding: 15px; margin-bottom: 15px; }
                .review-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
                .review-id { font-family: monospace; color: #666; font-size: 0.9em; }
                .review-status { padding: 4px 8px; border-radius: 4px; font-size: 0.8em; font-weight: bold; }
                .status-pending { background: #fff3cd; color: #856404; }
                .status-approved { background: #d4edda; color: #155724; }
                .status-rejected { background: #f8d7da; color: #721c24; }
                .status-modified { background: #d1ecf1; color: #0c5460; }
                .review-meta { color: #666; font-size: 0.9em; margin-bottom: 10px; }
                .btn { background: #007bff; color: white; padding: 6px 12px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; font-size: 0.9em; }
                .btn:hover { background: #0056b3; }
                .clearfix::after { content: ""; display: table; clear: both; }
            </style>
        </head>
        <body>
            <div class="header clearfix">
                <h1>All Reviews</h1>
                <div class="nav">
                    <a href="{{ url_for('index') }}">Dashboard</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                </div>
            </div>
            
            <div class="reviews-container">
                <h2>All Reviews ({{ all_reviews|length }})</h2>
                
                {% for review in all_reviews %}
                    <div class="review-item">
                        <div class="review-header">
                            <div>
                                <div class="review-id">{{ review.review_id }}</div>
                                <strong>{{ review.content_type }}</strong>
                            </div>
                            <div class="review-status status-{{ review.status.value }}">
                                {{ review.status.value.upper() }}
                            </div>
                        </div>
                        <div class="review-meta">
                            Created: {{ review.created_at.strftime('%Y-%m-%d %H:%M:%S') }}
                            {% if review.reviewed_at %}
                                | Reviewed: {{ review.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') }}
                            {% endif %}
                            {% if review.reviewer_username %}
                                | By: {{ review.reviewer_username }}
                            {% endif %}
                        </div>
                        <div>
                            <a href="{{ url_for('review_detail', review_id=review.review_id) }}" class="btn">View Details</a>
                        </div>
                    </div>
                {% endfor %}
            </div>
        </body>
        </html>
        """
        return render_template_string(template, all_reviews=all_reviews)
    
    def _render_review_detail(self, review_id: str):
        """Render detailed review page."""
        if review_id not in self.telegram_bot.reviews:
            return "Review not found", 404
        
        review = self.telegram_bot.reviews[review_id]
        
        template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Review {{ review.review_id }} - AI Instagram Publisher</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
                .header { background: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header h1 { margin: 0; color: #333; }
                .header .nav { float: right; }
                .header .nav a { color: #007bff; text-decoration: none; margin-left: 15px; }
                .review-container { display: grid; grid-template-columns: 1fr 300px; gap: 20px; }
                .review-content { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .review-actions { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .review-image { max-width: 100%; height: auto; border-radius: 8px; margin-bottom: 20px; }
                .review-caption { background: #f8f9fa; padding: 15px; border-radius: 4px; border-left: 4px solid #007bff; margin-bottom: 20px; white-space: pre-wrap; }
                .review-meta { color: #666; font-size: 0.9em; margin-bottom: 20px; }
                .review-status { padding: 8px 12px; border-radius: 4px; font-weight: bold; display: inline-block; margin-bottom: 20px; }
                .status-pending { background: #fff3cd; color: #856404; }
                .status-approved { background: #d4edda; color: #155724; }
                .status-rejected { background: #f8d7da; color: #721c24; }
                .status-modified { background: #d1ecf1; color: #0c5460; }
                .btn { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; text-decoration: none; display: inline-block; margin-right: 10px; margin-bottom: 10px; width: 100%; text-align: center; box-sizing: border-box; }
                .btn:hover { background: #0056b3; }
                .btn-success { background: #28a745; }
                .btn-success:hover { background: #218838; }
                .btn-danger { background: #dc3545; }
                .btn-danger:hover { background: #c82333; }
                .btn-warning { background: #ffc107; color: #212529; }
                .btn-warning:hover { background: #e0a800; }
                .modification-form { margin-top: 20px; }
                .form-group { margin-bottom: 15px; }
                .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
                .form-group textarea { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; min-height: 100px; }
                .clearfix::after { content: ""; display: table; clear: both; }
                @media (max-width: 768px) {
                    .review-container { grid-template-columns: 1fr; }
                }
            </style>
        </head>
        <body>
            <div class="header clearfix">
                <h1>Review Details</h1>
                <div class="nav">
                    <a href="{{ url_for('index') }}">Dashboard</a>
                    <a href="{{ url_for('reviews') }}">All Reviews</a>
                    <a href="{{ url_for('logout') }}">Logout</a>
                </div>
            </div>
            
            <div class="review-container">
                <div class="review-content">
                    <h2>{{ review.content_type }}</h2>
                    
                    <div class="review-meta">
                        <strong>Review ID:</strong> {{ review.review_id }}<br>
                        <strong>Created:</strong> {{ review.created_at.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                        {% if review.reviewed_at %}
                            <strong>Reviewed:</strong> {{ review.reviewed_at.strftime('%Y-%m-%d %H:%M:%S') }}<br>
                        {% endif %}
                        {% if review.reviewer_username %}
                            <strong>Reviewer:</strong> {{ review.reviewer_username }}<br>
                        {% endif %}
                    </div>
                    
                    <div class="review-status status-{{ review.status.value }}">
                        Status: {{ review.status.value.upper() }}
                    </div>
                    
                    {% if review.image_path %}
                        <img src="{{ url_for('serve_image', review_id=review.review_id) }}" alt="Review Image" class="review-image">
                    {% endif %}
                    
                    {% if review.caption %}
                        <div class="review-caption">{{ review.caption }}</div>
                    {% endif %}
                    
                    {% if review.modifications %}
                        <h3>Modifications</h3>
                        <pre>{{ review.modifications | tojson(indent=2) }}</pre>
                    {% endif %}
                </div>
                
                <div class="review-actions">
                    <h3>Actions</h3>
                    
                    {% if review.status.value == 'pending' %}
                        <button onclick="approveReview()" class="btn btn-success">✅ Approve</button>
                        <button onclick="rejectReview()" class="btn btn-danger">❌ Reject</button>
                        <button onclick="showModifyForm()" class="btn btn-warning">✏️ Modify</button>
                        
                        <div id="modify-form" class="modification-form" style="display: none;">
                            <h4>Modify Caption</h4>
                            <form onsubmit="modifyReview(event)">
                                <div class="form-group">
                                    <label for="new-caption">New Caption:</label>
                                    <textarea id="new-caption" name="caption" required>{{ review.caption or '' }}</textarea>
                                </div>
                                <button type="submit" class="btn">Save Changes</button>
                                <button type="button" onclick="hideModifyForm()" class="btn" style="background: #6c757d;">Cancel</button>
                            </form>
                        </div>
                    {% else %}
                        <p>This review has already been {{ review.status.value }}.</p>
                    {% endif %}
                </div>
            </div>
            
            <script>
                function approveReview() {
                    if (confirm('Are you sure you want to approve this content?')) {
                        fetch('/api/approve/{{ review.review_id }}', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    location.reload();
                                } else {
                                    alert('Error: ' + data.error);
                                }
                            });
                    }
                }
                
                function rejectReview() {
                    if (confirm('Are you sure you want to reject this content?')) {
                        fetch('/api/reject/{{ review.review_id }}', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                if (data.success) {
                                    location.reload();
                                } else {
                                    alert('Error: ' + data.error);
                                }
                            });
                    }
                }
                
                function showModifyForm() {
                    document.getElementById('modify-form').style.display = 'block';
                }
                
                function hideModifyForm() {
                    document.getElementById('modify-form').style.display = 'none';
                }
                
                function modifyReview(event) {
                    event.preventDefault();
                    const caption = document.getElementById('new-caption').value;
                    
                    fetch('/api/modify/{{ review.review_id }}', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ caption: caption })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            location.reload();
                        } else {
                            alert('Error: ' + data.error);
                        }
                    });
                }
            </script>
        </body>
        </html>
        """
        return render_template_string(template, review=review)
    
    def _handle_approval(self, review_id: str, status: ApprovalStatus):
        """Handle approval/rejection via API."""
        try:
            if review_id not in self.telegram_bot.reviews:
                return jsonify({'success': False, 'error': 'Review not found'})
            
            review = self.telegram_bot.reviews[review_id]
            
            if review.status != ApprovalStatus.PENDING:
                return jsonify({'success': False, 'error': 'Review already processed'})
            
            # Update review status
            review.status = status
            review.reviewed_at = datetime.now()
            review.reviewer_username = session.get('username', 'web_user')
            
            # Execute callback if provided
            if review.callback:
                try:
                    # Note: This is a sync call, in production you might want to use async
                    import asyncio
                    asyncio.create_task(review.callback(review, status))
                except Exception as e:
                    self.logger.error(f"Callback execution failed: {str(e)}")
            
            # Add to history
            self.telegram_bot._add_to_history(review)
            
            self.logger.info(
                f"Review {status.value} via web interface: {review_id}",
                extra={'extra_data': {
                    'review_id': review_id,
                    'status': status.value,
                    'reviewer': session.get('username')
                }}
            )
            
            return jsonify({'success': True})
            
        except Exception as e:
            self.logger.error(f"Error handling approval: {str(e)}")
            handle_exception(e, {"component": "web_review_approval"})
            return jsonify({'success': False, 'error': str(e)})
    
    def _handle_modification(self, review_id: str):
        """Handle modification via API."""
        try:
            if review_id not in self.telegram_bot.reviews:
                return jsonify({'success': False, 'error': 'Review not found'})
            
            review = self.telegram_bot.reviews[review_id]
            
            if review.status != ApprovalStatus.PENDING:
                return jsonify({'success': False, 'error': 'Review already processed'})
            
            # Get modification data
            data = request.get_json()
            new_caption = data.get('caption')
            
            if not new_caption:
                return jsonify({'success': False, 'error': 'Caption is required'})
            
            # Store original and update
            review.modifications['original_caption'] = review.caption
            review.caption = new_caption
            review.status = ApprovalStatus.MODIFIED
            review.reviewed_at = datetime.now()
            review.reviewer_username = session.get('username', 'web_user')
            
            # Execute callback if provided
            if review.callback:
                try:
                    import asyncio
                    asyncio.create_task(review.callback(review, ApprovalStatus.MODIFIED))
                except Exception as e:
                    self.logger.error(f"Callback execution failed: {str(e)}")
            
            # Add to history
            self.telegram_bot._add_to_history(review)
            
            self.logger.info(
                f"Review modified via web interface: {review_id}",
                extra={'extra_data': {
                    'review_id': review_id,
                    'reviewer': session.get('username'),
                    'original_caption': review.modifications['original_caption'][:100],
                    'new_caption': new_caption[:100]
                }}
            )
            
            return jsonify({'success': True})
            
        except Exception as e:
            self.logger.error(f"Error handling modification: {str(e)}")
            handle_exception(e, {"component": "web_review_modification"})
            return jsonify({'success': False, 'error': str(e)})
    
    def run(self, host='127.0.0.1', port=5000, debug=False):
        """Run the Flask application."""
        try:
            self.logger.info(f"Starting web review interface on {host}:{port}")
            self.app.run(host=host, port=port, debug=debug)
        except Exception as e:
            self.logger.error(f"Failed to start web interface: {str(e)}")
            raise


# Global web interface instance
_web_interface = None


def get_web_interface() -> WebReviewInterface:
    """Get or create the global web interface instance."""
    global _web_interface
    if _web_interface is None:
        _web_interface = WebReviewInterface()
    return _web_interface


# Convenience function to start the web interface
def start_web_interface(host='127.0.0.1', port=5000, debug=False):
    """Start the web review interface.
    
    Args:
        host: Host to bind to
        port: Port to bind to
        debug: Enable debug mode
    """
    interface = get_web_interface()
    interface.run(host=host, port=port, debug=debug)


if __name__ == '__main__':
    start_web_interface(debug=True)