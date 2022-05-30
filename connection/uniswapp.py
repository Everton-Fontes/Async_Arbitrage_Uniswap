"""https:thegraph.com/hosted-service/subgraph/uniswap/uniswap-v3"""
import json
import aiohttp


class Uniswap_GraphQL:
    def __init__(self) -> None:
        self.url = 'https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3'
        self.query = ''

    async def post(self, url: str, params: dict = None, jsonn: dict = None) -> dict:
        if not isinstance(url, str):
            return
        if url == '':
            return
        if params:
            assert type(params) == dict

        async with aiohttp.ClientSession() as session:
            if params:
                async with session.post(url=url, params=params) as resp:
                    if resp.status == 200:
                        data = json.loads(await resp.text())
                        return data
            if jsonn:
                async with session.post(url=url, json=jsonn,  headers={'Content-Type': 'application/json'}) as resp:
                    if resp.status == 200:
                        data = json.loads(await resp.text())
                        return data['data']

    async def retrieve_info(self) -> list:
        self.query = """
         {
              pools (orderBy: totalValueLockedETH,
                orderDirection: desc,
                first:500) {
                id
                totalValueLockedETH
                token0Price
                token1Price
                feeTier
                token0 {id symbol name decimals}
                token1 {id symbol name decimals}
                }
              }
        """
        data = await self.post(self.url, jsonn={'query': self.query})
        return data['pools']
