import json
import unittest
from unittest.mock import patch

from agent import run_agent
from decisions import get_next_action, validate_decision
from llm import ask_llm
from state import AgentState


class DecisionTests(unittest.TestCase):
    def test_valid_actions(self):
        for action in ({'action':'search', 'query':' topic '},
                       {'action':'fetch', 'url':'https://example.com/article'},
                       {'action':'finish', 'answer':'Insufficient evidence.'}):
            result = validate_decision(json.dumps(action))
            self.assertEqual(result['action'], action['action'])
        self.assertEqual(validate_decision('{"action":"search","query":" topic "}')['query'], 'topic')

    def test_invalid_actions(self):
        values = ['not JSON', '[]', '{}', '{"action": []}',
                  '{"action":"shell","command":"ls"}',
                  '{"action":"search","query":" "}',
                  '{"action":"search","query":1}',
                  '{"action":"finish"}',
                  '{"action":"finish","answer":"ok","extra":true}',
                  '{"action":"fetch","url":"file:///etc/hosts"}',
                  '{"action":"fetch","url":"https://"}']
        for value in values:
            with self.subTest(value=value), self.assertRaises(ValueError):
                validate_decision(value)

    def test_one_repair_attempt(self):
        with patch('decisions.ask_llm', side_effect=['invalid', '{"action":"search","query":"topic"}']) as model:
            self.assertEqual(get_next_action(AgentState())['action'], 'search')
            self.assertEqual(model.call_count, 2)
        with patch('decisions.ask_llm', return_value='invalid') as model:
            with self.assertRaisesRegex(RuntimeError, 'twice'):
                get_next_action(AgentState())
            self.assertEqual(model.call_count, 2)

    def test_loop_feeds_evidence_back_to_model(self):
        state = AgentState()
        state.question = 'A research question'
        replies = iter([
            '{"action":"search","query":"specific query"}',
            '{"action":"fetch","url":"https://example.com/article"}',
            '{"action":"finish","answer":"A brief [source](https://example.com/article)"}',
        ])
        contexts = []
        def model(messages, **kwargs):
            contexts.append(json.loads(messages[1]['content']))
            return next(replies)
        with patch('decisions.ask_llm', side_effect=model), patch('agent.search_web', return_value=[{'url':'https://example.com/article'}]), patch('agent.fetch_page', return_value={'content':'Evidence from the page'}):
            self.assertIn('A brief', run_agent(state))
        self.assertEqual(contexts[0]['question'], state.question)
        self.assertEqual(contexts[1]['history'][0]['decision']['query'], 'specific query')
        self.assertEqual(contexts[2]['sources'][0]['content'], 'Evidence from the page')
        self.assertEqual(state.steps, 2)

    def test_step_limit(self):
        with patch('agent.MAX_STEPS', 1), patch('agent.get_next_action', return_value={'action':'search', 'query':'topic'}), patch('agent.search_web', return_value=[]):
            self.assertIn('step limit', run_agent(AgentState()))

    def test_json_mode_is_sent_to_ollama(self):
        with patch('llm.requests.post') as request:
            request.return_value.json.return_value = {"message": {"content": "{}"}}
            ask_llm([], model='test', json_mode=True)
        self.assertEqual(request.call_args.kwargs['json']['format'], 'json')


if __name__ == '__main__':
    unittest.main()
