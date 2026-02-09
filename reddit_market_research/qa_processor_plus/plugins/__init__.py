"""
Plugin Configuration Module

This module provides configuration and management for QA processor plugins,
allowing dynamic loading and configuration of plugin components.
"""

from typing import List, Dict, Any, Optional
from .base import BasePlugin


class PluginManager:
    """Manages QA processor plugins."""
    
    def __init__(self):
        """Initialize the plugin manager."""
        self.plugins = []
        self.enabled_plugins = []
    
    def load_plugin(self, plugin_class: type, **kwargs) -> BasePlugin:
        """
        Load a plugin.
        
        Args:
            plugin_class: Plugin class to load
            **kwargs: Arguments for plugin initialization
            
        Returns:
            Loaded plugin instance
        """
        plugin = plugin_class(**kwargs)
        self.plugins.append(plugin)
        return plugin
    
    def enable_plugin(self, plugin: BasePlugin) -> None:
        """Enable a plugin."""
        if plugin not in self.enabled_plugins:
            self.enabled_plugins.append(plugin)
            plugin.enable()
    
    def disable_plugin(self, plugin: BasePlugin) -> None:
        """Disable a plugin."""
        if plugin in self.enabled_plugins:
            self.enabled_plugins.remove(plugin)
            plugin.disable()
    
    def get_enabled_plugins(self) -> List[BasePlugin]:
        """Get list of enabled plugins.
        
        Returns:
            List of enabled plugins
        """
        return self.enabled_plugins
    
    def get_all_plugins(self) -> List[BasePlugin]:
        """Get list of all loaded plugins.
        
        Returns:
            List of all plugins
        """
        return self.plugins
    
    def process_with_plugins(self, conversations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Process conversations with all enabled plugins.
        
        Args:
            conversations: List of QA conversations
            
        Returns:
            Processed conversations
        """
        for plugin in self.enabled_plugins:
            if plugin.is_plugin_enabled():
                conversations = plugin.process(conversations)
        return conversations
    
    def get_plugin_info(self) -> List[Dict[str, Any]]:
        """
        Get information about all plugins.
        
        Returns:
            List of plugin information dictionaries
        """
        return [plugin.get_info() for plugin in self.plugins]