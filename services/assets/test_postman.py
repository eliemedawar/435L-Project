"""Check the Assets collection packaging. Developed by: Marc Bteich.

These checks do not execute Postman's JavaScript or replace a Postman run.
"""
import json
from pathlib import Path
import unittest


class PostmanCollectionTests(unittest.TestCase):
    def test_collection_attribution_variables_and_route_coverage(self):
        root = Path(__file__).resolve().parents[2]
        collection = json.loads((root/'postman/assets.postman_collection.json').read_text())
        self.assertEqual(collection['info']['schema'],
                         'https://schema.getpostman.com/json/collection/v2.1.0/collection.json')
        requests = [item for folder in collection['item'] for item in folder['item']]
        self.assertEqual(len(requests), 50)
        routes = {(item['request']['method'], item['request']['url']) for item in requests}
        for method, path in [('POST','/assets'),('PUT','/assets/{{asset_id}}'),
                             ('DELETE','/assets/{{asset_id}}'),('GET','/assets'),
                             ('GET','/assets/{{asset_id}}'),('GET','/internal/stats'),
                             ('GET','/internal/assets/{{asset_id}}')]:
            self.assertIn((method, '{{base_assets}}'+path), routes)
        variables = {v['key']:v['value'] for v in collection['variable']}
        for key,value in variables.items():
            if key.endswith('_password') or key.startswith('token_') or key=='service_key':
                self.assertEqual(value, '', key)
        for item in requests:
            self.assertIn('Marc Bteich', item['request']['description'])
            self.assertTrue(item['event'][0]['script']['exec'])
            for header in item['request']['header']:
                if header['key'] in ('Authorization','X-Service-Key'):
                    self.assertIn('{{', header['value'])
        statuses = '\n'.join(item['request']['description'] for item in requests)
        for code in (200,201,400,401,403,404,409):
            self.assertIn(f'HTTP {code}', statuses)


if __name__ == '__main__':
    unittest.main()
