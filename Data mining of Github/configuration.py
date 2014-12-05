# -*- coding: utf-8 -*-
"""Contains the configuration for the program."""
import ConfigParser


class Configuration(object):

    """Configuration to Github mining."""

    def __init__(self, filename):
        """Set the default values and reads and parses the file."""
        default_values = {'save_path': '',
                          'number_of_repos': 100,
                          'number_of_users': 100}
        self.config = ConfigParser.ConfigParser(default_values)
        self.config.read(filename)

    @property
    def git_user(self):
        """Get configurated Github.com username."""
        return self.config.get('Github', 'user')

    @property
    def git_password(self):
        """Get configurated Github.com password."""
        return self.config.get('Github', 'password')

    @property
    def user_agent(self):
        """Get configurated Github.com user-agent."""
        return self.config.get('Github', 'user-agent')

    @property
    def graph_save_path(self):
        """Get save path to generated graphs."""
        return self.config.get('Graph', 'save_path').strip()

    @property
    def graph_start_repos(self):
        """Get the repositories to start with."""
        return [repo.strip()
                for repo
                in self.config.get('Graph', 'start_repos').split(',')]

    @property
    def graph_number_of_repos(self):
        """Get the number of repositories the crawler finds."""
        return int(self.config.get('Graph', 'number_of_repos').strip())

    @property
    def graph_number_of_users(self):
        """Get the number of Github.com users the crawler finds."""
        return int(self.config.get('Graph', 'number_of_users').strip())
