"""
Dependency Injection Container for AI Socials.

This module provides a simple but effective dependency injection container
for managing dependencies and improving testability.
"""

import inspect
import functools
from typing import Dict, Any, Type, TypeVar, Callable, Optional, Union
from abc import ABC, abstractmethod

from utils.logger import get_logger
from utils.exceptions import ValidationError


T = TypeVar('T')


class ServiceContainer:
    """Simple dependency injection container."""

    def __init__(self):
        """Initialize the container."""
        self.logger = get_logger(__name__)
        self._services: Dict[str, Any] = {}
        self._singletons: Dict[str, Any] = {}
        self._factories: Dict[str, Callable] = {}
        self._interfaces: Dict[str, Type] = {}

    def register_singleton(self, service_type: Union[Type[T], str], instance: T) -> 'ServiceContainer':
        """Register a singleton instance.

        Args:
            service_type: Service type or name
            instance: Service instance

        Returns:
            Self for chaining
        """
        key = self._get_service_key(service_type)
        self._singletons[key] = instance
        self.logger.debug(f"Registered singleton: {key}")
        return self

    def register_transient(self, service_type: Union[Type[T], str], factory: Callable[[], T]) -> 'ServiceContainer':
        """Register a transient service (new instance each time).

        Args:
            service_type: Service type or name
            factory: Factory function to create instances

        Returns:
            Self for chaining
        """
        key = self._get_service_key(service_type)
        self._factories[key] = factory
        self.logger.debug(f"Registered transient: {key}")
        return self

    def register_scoped(self, service_type: Union[Type[T], str], factory: Callable[[], T]) -> 'ServiceContainer':
        """Register a scoped service (singleton within a scope).

        For now, this behaves like singleton. In a web context, 
        this could be per-request scoping.

        Args:
            service_type: Service type or name
            factory: Factory function to create instances

        Returns:
            Self for chaining
        """
        key = self._get_service_key(service_type)

        def scoped_factory():
            if key not in self._services:
                self._services[key] = factory()
            return self._services[key]

        self._factories[key] = scoped_factory
        self.logger.debug(f"Registered scoped: {key}")
        return self

    def register_interface(self, interface_type: Type, implementation_type: Type) -> 'ServiceContainer':
        """Register an interface to implementation mapping.

        Args:
            interface_type: Interface/abstract class
            implementation_type: Concrete implementation

        Returns:
            Self for chaining
        """
        interface_key = self._get_service_key(interface_type)
        impl_key = self._get_service_key(implementation_type)

        self._interfaces[interface_key] = implementation_type

        # Auto-register the implementation as transient if not already registered
        if impl_key not in self._singletons and impl_key not in self._factories:
            self.register_transient(implementation_type, lambda: self._create_instance(implementation_type))

        self.logger.debug(f"Registered interface mapping: {interface_key} -> {impl_key}")
        return self

    def resolve(self, service_type: Union[Type[T], str]) -> T:
        """Resolve a service instance.

        Args:
            service_type: Service type or name to resolve

        Returns:
            Service instance

        Raises:
            ValidationError: If service cannot be resolved
        """
        key = self._get_service_key(service_type)

        # Check singletons first
        if key in self._singletons:
            return self._singletons[key]

        # Check factories
        if key in self._factories:
            return self._factories[key]()

        # Check interface mappings
        if key in self._interfaces:
            impl_type = self._interfaces[key]
            return self.resolve(impl_type)

        # Try to auto-resolve if it's a class
        if inspect.isclass(service_type):
            try:
                return self._create_instance(service_type)
            except Exception as e:
                raise ValidationError(
                    f"Cannot auto-resolve service: {key}",
                    details={"service_type": key, "error": str(e)}
                )

        raise ValidationError(
            f"Service not registered: {key}",
            details={"service_type": key, "available_services": list(self._singletons.keys()) + list(self._factories.keys())}
        )

    def _create_instance(self, service_type: Type[T]) -> T:
        """Create an instance with dependency injection.

        Args:
            service_type: Type to instantiate

        Returns:
            New instance with dependencies injected
        """
        # Get constructor signature
        sig = inspect.signature(service_type.__init__)

        # Prepare arguments for constructor
        kwargs = {}
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue

            # Try to resolve the parameter type
            if param.annotation != inspect.Parameter.empty:
                try:
                    kwargs[param_name] = self.resolve(param.annotation)
                except ValidationError:
                    # If we can't resolve and there's no default, raise error
                    if param.default == inspect.Parameter.empty:
                        raise ValidationError(
                            f"Cannot resolve dependency: {param_name} of type {param.annotation}",
                            details={"service_type": service_type.__name__, "parameter": param_name}
                        )

        return service_type(**kwargs)

    def _get_service_key(self, service_type: Union[Type, str]) -> str:
        """Get a string key for a service type."""
        if isinstance(service_type, str):
            return service_type
        elif hasattr(service_type, '__name__'):
            return f"{service_type.__module__}.{service_type.__name__}"
        else:
            return str(service_type)

    def list_services(self) -> Dict[str, str]:
        """List all registered services.

        Returns:
            Dictionary of service names and their types
        """
        services = {}

        for key in self._singletons:
            services[key] = "singleton"

        for key in self._factories:
            services[key] = "transient/scoped"

        for key, impl_type in self._interfaces.items():
            services[key] = f"interface -> {self._get_service_key(impl_type)}"

        return services

    def clear(self):
        """Clear all registered services."""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()
        self._interfaces.clear()
        self.logger.debug("Container cleared")


# Service interfaces for better abstraction
class IImageGenerator(ABC):
    """Interface for image generators."""

    @abstractmethod
    def generate_image(self, prompt: str, output_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Generate an image."""
        pass


class ICaptionGenerator(ABC):
    """Interface for caption generators."""

    @abstractmethod
    def generate_caption(self, prompt: str, style: str = "engaging", **kwargs) -> Dict[str, Any]:
        """Generate a caption."""
        pass


class IInstagramPublisher(ABC):
    """Interface for Instagram publishers."""

    @abstractmethod
    def publish_post(self, image_path: str, caption: str, **kwargs) -> Dict[str, Any]:
        """Publish a post to Instagram."""
        pass


class IContentScheduler(ABC):
    """Interface for content schedulers."""

    @abstractmethod
    def add_job(self, function: Callable, job_type: Any, **kwargs) -> str:
        """Add a scheduled job."""
        pass

    @abstractmethod
    def start(self):
        """Start the scheduler."""
        pass

    @abstractmethod
    def stop(self, wait: bool = True):
        """Stop the scheduler."""
        pass


class ITelegramBot(ABC):
    """Interface for Telegram bots."""

    @abstractmethod
    async def submit_for_review(self, content_type: str, **kwargs) -> str:
        """Submit content for review."""
        pass


# Global container instance
_container = None


def get_container() -> ServiceContainer:
    """Get or create the global service container."""
    global _container
    if _container is None:
        _container = ServiceContainer()
        _setup_default_services()
    return _container


def _setup_default_services():
    """Set up default service registrations."""
    container = _container

    try:
        # Register core services with their interfaces
        services_to_register = []

        # Try to import each service individually
        try:
            from generator.image_generator import ImageGenerator
            services_to_register.append(('ImageGenerator', ImageGenerator, lambda: ImageGenerator()))
            container.logger.debug("ImageGenerator imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import ImageGenerator: {str(e)}")

        try:
            from generator.caption_generator import CaptionGenerator
            services_to_register.append(('CaptionGenerator', CaptionGenerator, lambda: CaptionGenerator()))
            container.logger.debug("CaptionGenerator imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import CaptionGenerator: {str(e)}")

        try:
            from generator.ollama_caption_generator import OllamaCaptionGenerator
            services_to_register.append(('OllamaCaptionGenerator', OllamaCaptionGenerator, lambda: OllamaCaptionGenerator()))
            container.logger.debug("OllamaCaptionGenerator imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import OllamaCaptionGenerator: {str(e)}")

        try:
            from publisher.instagram_publisher import InstagramPublisher
            services_to_register.append(('InstagramPublisher', InstagramPublisher, lambda: InstagramPublisher()))
            container.logger.debug("InstagramPublisher imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import InstagramPublisher: {str(e)}")

        try:
            from scheduler.scheduler import ContentScheduler
            services_to_register.append(('ContentScheduler', ContentScheduler, lambda: ContentScheduler()))
            container.logger.debug("ContentScheduler imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import ContentScheduler: {str(e)}")

        try:
            from reviewer.telegram_bot import TelegramReviewBot
            services_to_register.append(('TelegramReviewBot', TelegramReviewBot, lambda: TelegramReviewBot()))
            container.logger.debug("TelegramReviewBot imported successfully")
        except Exception as e:
            container.logger.warning(f"Failed to import TelegramReviewBot: {str(e)}")

        # Register successfully imported services
        for name, service_type, factory in services_to_register:
            try:
                container.register_transient(service_type, factory)
                container.logger.debug(f"Registered {name} successfully")
            except Exception as e:
                container.logger.warning(f"Failed to register {name}: {str(e)}")

        # Register caption generator factory that selects based on configuration
        def caption_generator_factory():
            from config import get_config
            config = get_config()
            if config.caption_generator == "ollama":
                return OllamaCaptionGenerator()
            else:
                return CaptionGenerator()

        container.register_transient('caption_generator', caption_generator_factory)

        # Register interface mappings for successfully imported services
        for name, service_type, factory in services_to_register:
            try:
                if name == 'ImageGenerator':
                    container.register_interface(IImageGenerator, service_type)
                elif name == 'InstagramPublisher':
                    container.register_interface(IInstagramPublisher, service_type)
                elif name == 'ContentScheduler':
                    container.register_interface(IContentScheduler, service_type)
                elif name == 'TelegramReviewBot':
                    container.register_interface(ITelegramBot, service_type)
            except Exception as e:
                container.logger.warning(f"Failed to register interface for {name}: {str(e)}")

        # Map ICaptionGenerator to the factory service key
        container._interfaces[container._get_service_key(ICaptionGenerator)] = 'caption_generator'

        # Register configuration as singleton
        try:
            from config import get_config
            container.register_singleton('config', get_config())
        except Exception as e:
            container.logger.warning(f"Failed to register config: {str(e)}")

        container.logger.info("Default services registration completed")

    except Exception as e:
        container.logger.error(f"Critical error in service registration: {str(e)}")


# Convenience functions
def resolve(service_type: Union[Type[T], str]) -> T:
    """Resolve a service from the global container."""
    return get_container().resolve(service_type)


def register_singleton(service_type: Union[Type[T], str], instance: T) -> ServiceContainer:
    """Register a singleton in the global container."""
    return get_container().register_singleton(service_type, instance)


def register_transient(service_type: Union[Type[T], str], factory: Callable[[], T]) -> ServiceContainer:
    """Register a transient service in the global container."""
    return get_container().register_transient(service_type, factory)


def register_interface(interface_type: Type, implementation_type: Type) -> ServiceContainer:
    """Register an interface mapping in the global container."""
    return get_container().register_interface(interface_type, implementation_type)


# Decorator for dependency injection
def inject(**dependencies):
    """Decorator for automatic dependency injection.

    Usage:
        @inject(image_gen=IImageGenerator, caption_gen=ICaptionGenerator)
        def my_function(image_gen, caption_gen, other_param):
            # image_gen and caption_gen will be automatically resolved
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            container = get_container()

            # Resolve dependencies
            for param_name, service_type in dependencies.items():
                if param_name not in kwargs:
                    kwargs[param_name] = container.resolve(service_type)

            return func(*args, **kwargs)
        return wrapper
    return decorator


# Context manager for scoped services
class ServiceScope:
    """Context manager for service scoping."""

    def __init__(self, container: Optional[ServiceContainer] = None):
        self.container = container or get_container()
        self._original_services = None

    def __enter__(self):
        # Save current scoped services
        self._original_services = self.container._services.copy()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore original scoped services
        self.container._services = self._original_services


if __name__ == '__main__':
    # Example usage
    container = get_container()

    print("Registered services:")
    for service, service_type in container.list_services().items():
        print(f"  {service}: {service_type}")
