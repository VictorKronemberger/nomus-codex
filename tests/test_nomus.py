import asyncio
import json
import os
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

os.environ["NOMUS_BASE_URL"] = "https://erp.example.com/demo/rest"
import nomus_server as server

REAL_CLIENT = httpx.Client


class NomusTests(unittest.TestCase):
    def setUp(self):
        self.env = patch.dict(os.environ, {"NOMUS_API_KEY": "test-key-not-real"})
        self.env.start()
        self.addCleanup(self.env.stop)

    def transport(self, handler):
        return patch.object(server.httpx, "Client",
                            side_effect=lambda **kw: REAL_CLIENT(transport=httpx.MockTransport(handler), **kw))

    def test_credential_and_pagination(self):
        seen = []
        def handler(req):
            seen.append(req)
            self.assertEqual(str(req.url.copy_with(query=None)), server.BASE_URL + "/produtos")
            self.assertEqual(req.headers["Authorization"], "Basic test-key-not-real")
            self.assertEqual(req.url.params["pagina"], "2")
            self.assertEqual(req.url.params["query"], "codigo==ABC")
            return httpx.Response(200, json=[{"id": 1}])
        with self.transport(handler):
            result = server.nomus_consultar("produtos", 2, "codigo==ABC")
        self.assertEqual(result["dados"], [{"id": 1}])
        self.assertEqual(len(seen), 1)

    def test_blocks_non_catalog_routes_before_network(self):
        with patch.object(server.httpx, "Client") as client:
            for path in ["https://evil.test", "../usuarios", "produtos/%2e%2e", "produtos?x=1", "desconhecido"]:
                with self.subTest(path=path), self.assertRaises(ValueError):
                    server.nomus_consultar(path)
            client.assert_not_called()

    def test_blocks_invalid_destination_before_network(self):
        invalid = ["", "http://erp.example.com/demo/rest",
                   "https://user:password@erp.example.com/demo/rest",
                   "https://erp.example.com/demo/Login.do",
                   "https://erp.example.com/demo/rest?secret=example",
                   "https://erp.example.com/demo/rest#fragment"]
        with patch.object(server.httpx, "Client") as client:
            for url in invalid:
                with self.subTest(url=url), patch.object(server, "BASE_URL", url):
                    with self.assertRaisesRegex(ValueError, "NOMUS_BASE_URL"):
                        server.nomus_consultar("produtos")
            client.assert_not_called()

    def test_missing_credentials(self):
        with patch.dict(os.environ, {"NOMUS_API_KEY": ""}):
            with self.assertRaisesRegex(ValueError, "Chave ausente"):
                server.nomus_consultar("produtos")

    def test_auth_and_redirects_never_retried(self):
        for status in (302, 401, 403, 429, 500):
            calls = []
            def handler(req):
                calls.append(req)
                return httpx.Response(status, headers={"Location": "https://evil.test"},
                                      text="test-key-not-real")
            with self.subTest(status=status), self.transport(handler):
                with self.assertRaises(ValueError) as error:
                    server.nomus_consultar("produtos")
                self.assertNotIn("test-key-not-real", str(error.exception))
                self.assertEqual(len(calls), 1)

    def test_write_payload_and_no_retry(self):
        calls = []
        def handler(req):
            calls.append(req)
            self.assertEqual(req.method, "POST")
            self.assertEqual(json.loads(req.content), {"nome": "Teste"})
            raise httpx.ReadTimeout("simulated")
        with self.transport(handler):
            with self.assertRaisesRegex(ValueError, "incerto"):
                server.nomus_executar("POST", "produtos", {"nome": "Teste"})
        self.assertEqual(len(calls), 1)

    def test_rejects_empty_write(self):
        with patch.object(server.httpx, "Client") as client:
            with self.assertRaises(ValueError):
                server.nomus_executar("POST", "produtos")
            client.assert_not_called()

    def test_redaction_and_non_json(self):
        with self.transport(lambda req: httpx.Response(200, json={"echo": "test-key-not-real"})):
            self.assertEqual(server.nomus_consultar("produtos")["dados"]["echo"], "[CHAVE_OCULTA]")
        with self.transport(lambda req: httpx.Response(200, text="<html>Login</html>")):
            with self.assertRaisesRegex(ValueError, "sem JSON"):
                server.nomus_consultar("produtos")

    def test_mcp_stdio(self):
        async def run():
            params = StdioServerParameters(command=sys.executable,
                args=[str(Path(server.__file__).resolve())], env={"NOMUS_API_KEY": "", "NOMUS_BASE_URL": server.BASE_URL})
            async with stdio_client(params) as (read, write):
                async with ClientSession(read, write) as client:
                    await client.initialize()
                    listing = await client.list_tools()
                    by_name = {tool.name: tool for tool in listing.tools}
                    self.assertEqual(set(by_name), {
                        "nomus_status", "nomus_catalogo", "nomus_consultar", "nomus_executar"})
                    self.assertTrue(by_name["nomus_consultar"].annotations.readOnlyHint)
                    self.assertFalse(by_name["nomus_executar"].annotations.readOnlyHint)
                    result = await client.call_tool("nomus_status", {})
                    self.assertFalse(result.isError)
                    data = json.loads(result.content[0].text)
                    self.assertFalse(data["chave_configurada"])
                    result = await client.call_tool("nomus_catalogo", {"busca": "saldosEstoqueProduto"})
                    self.assertFalse(result.isError)
                    result = await client.call_tool("nomus_consultar", {"caminho": "produtos"})
                    self.assertTrue(result.isError)
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
