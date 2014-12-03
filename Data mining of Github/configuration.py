import ConfigParser


class Configuration(object):
    """description of class"""

    def __init__(self, filename):
        default_values = {'port': '27017', 
                          'save_path': '',
                          'number_of_repos': 100,
                          'number_of_users': 100}
        self.config = ConfigParser.ConfigParser(default_values)
        self.config.read(filename)

    @property
    def db_user(self):
        return self.config.get('Database', 'user')

    @property
    def db_password(self):
        return self.config.get('Database', 'password')

    @property
    def db_host(self):
        return self.config.get('Database', 'host')

    @property
    def db_port(self):
        return self.config.get('Database', 'port')

    @property
    def db_database(self):
        return self.config.get('Database', 'database')

    @property
    def git_user(self):
        return self.config.get('Github', 'user')

    @property
    def git_password(self):
        return self.config.get('Github', 'password')

    @property
    def user_agent(self):
        return self.config.get('Github', 'user-agent')

    @property
    def graph_save_path(self):
        return self.config.get('Graph', 'save_path').strip()

    @property
    def graph_start_repos(self):
        return [repo.strip()
                for repo
                in self.config.get('Graph', 'start_repos').split(',')]

    @property
    def graph_number_of_repos(self):
        return int(self.config.get('Graph', 'number_of_repos').strip())

    @property
    def graph_number_of_users(self):
        return int(self.config.get('Graph', 'number_of_users').strip())
