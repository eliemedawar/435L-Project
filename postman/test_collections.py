"""Verify merge preservation and attribution. Developed by: Marc Bteich."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class CollectionTests(unittest.TestCase):
    def test_elie_requests_and_collection_hooks_preserved(self):
        merged=json.loads((ROOT/'postman/SIDRMS.postman_collection.json').read_text())
        folders={item['name']:item for item in merged['item']}
        for name in ('users','incidents','logs','notifications','reports_a'):
            original=json.loads((ROOT/f'postman/{name}.postman_collection.json').read_text())
            items=folders[name]['item']
            if name=='incidents':
                items=items[1:]
            self.assertEqual(items,original['item'],name)
            for key in ('auth','event'):
                self.assertEqual(folders[name].get(key),original.get(key),(name,key))
        for name in ('assets','threats','vulnerabilities','playbooks','reports_b'):
            source=json.loads((ROOT/f'postman/{name}.postman_collection.json').read_text())
            def walk(items):
                for item in items:
                    if 'item' in item:
                        yield from walk(item['item'])
                    else:
                        yield item
            for request in walk(source['item']):
                self.assertIn('Marc Bteich',request['request']['description'])
