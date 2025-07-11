from result_parsers.code_executor import Executor
from result_parsers.code_executor_persist import ExecutorPersist
from result_parsers.text_parser import TextResultParser
from result_parsers.box_parser import BoxParser

class ResultParser:
    """
    A result parser interface that can parse results from boxed, json, and code.
    """
    def __init__(self, config):
        self.config = config
        self.mode = config.mode
        self.pot = Executor(config)
        self.tot = TextResultParser(config)
        self.scot = ExecutorPersist(config)
        self.box_parser = BoxParser(config)
        
    def parse(self, samples, parse_mode):  # 'code', 'code_persist', 'json', 'boxed'
        if parse_mode == 'code':
            return self.pot.execute(samples)
        elif parse_mode == 'code_persist':
            return self.scot.execute(samples)
        elif parse_mode == 'json':
            return self.tot.execute(samples)
        elif parse_mode == 'boxed':
            return self.box_parser.execute(samples)
        else:
            assert False