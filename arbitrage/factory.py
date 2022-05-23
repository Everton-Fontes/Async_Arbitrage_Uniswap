from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass, field
import json
from arbitrage.pairs import *


@dataclass
class Factory_Arbitrage(ABC):
    __value: float
    __fee: float
    __min_surface_rate: float
    __pairs: list[Pair] = field(default_factory=list)
    __duplicate: list = field(default_factory=list)
    __triangular_pair_list: list[Triangles_pair] = field(default_factory=list)

    @property
    def pairs(self):
        return self.__pairs

    def add_pairs(self, pair_inst: Pair) -> None:
        self.__pairs.append(pair_inst)

    async def _add_pairs(self, pair_inst: Pair) -> None:
        self.__pairs.append(pair_inst)

    @property
    def value(self):
        return self.__value

    @property
    def fee(self):
        return self.__fee

    @property
    def min_surface_rate(self):
        return self.__min_surface_rate

    async def duplicate(self) -> list:
        return self.__duplicate

    async def add_duplicate(self, add) -> None:
        self.__duplicate.append(add)

    async def triangular_pair_list(self) -> list[Triangles_pair]:
        return self.__triangular_pair_list

    async def add_triangular_pair_list(self, add: Triangles_pair):
        self.__triangular_pair_list.append(add)

    async def _get_triangules(self) -> None:
        # get pair_b
        for pair_a in self.pairs:
            a_box = [pair_a.base.symbol, pair_a.quote.symbol]
            for pair_b in self.pairs:

                if pair_a.pair != pair_b.pair:
                    if pair_b.base.symbol in a_box or pair_b.quote.symbol in a_box:

                        for pair_c in self.pairs:
                            if pair_c.pair != pair_a.pair and pair_c.pair != pair_b.pair:
                                combine_all = [
                                    pair_a.pair,
                                    pair_b.pair,
                                    pair_c.pair
                                ]

                                pair_box = [
                                    pair_a.base.symbol,
                                    pair_a.quote.symbol,
                                    pair_b.base.symbol,
                                    pair_b.quote.symbol,
                                    pair_c.base.symbol,
                                    pair_c.quote.symbol,
                                ]

                                # check triangle
                                count_base = 0
                                count_quote = 0
                                for i in pair_box:
                                    if i == pair_c.base.symbol:
                                        count_base += 1
                                    if i == pair_c.quote.symbol:
                                        count_quote += 1

                                if count_quote == 2 and count_base == 2 and pair_c.base.symbol != pair_c.quote.symbol:
                                    unique_item = ''.join(sorted(combine_all))
                                    duplicate = await self.duplicate()
                                    if unique_item not in duplicate:
                                        match = Triangles_pair(
                                            pair_a, pair_b, pair_c)
                                        await self.add_duplicate(unique_item)
                                        await self.add_triangular_pair_list(match)

    async def save_triangular_list(self):
        t = await self.triangular_pair_list()
        with open('structured_triangules_uniswap.json', 'w') as file:
            file.write(json.dumps([
                {'pair_a': {
                    'address': tri.pair_a.address,
                    'base': {'symbol': tri.pair_a.base.symbol,
                             'address': tri.pair_a.base.symbol,
                             'decimals': tri.pair_a.base.decimals,
                             },
                    'quote': {'symbol': tri.pair_a.quote.symbol,
                              'address': tri.pair_a.quote.symbol,
                              'decimals': tri.pair_a.quote.decimals,
                              }
                },
                    'pair_b': {
                        'address': tri.pair_b.address,
                        'base': {'symbol': tri.pair_b.base.symbol,
                                 'address': tri.pair_b.base.symbol,
                                 'decimals': tri.pair_b.base.decimals,
                                 },
                        'quote': {'symbol': tri.pair_b.quote.symbol,
                                  'address': tri.pair_b.quote.symbol,
                                  'decimals': tri.pair_b.quote.decimals,
                                  }
                },
                    'pair_c': {
                        'address': tri.pair_c.address,
                        'base': {'symbol': tri.pair_c.base.symbol,
                                 'address': tri.pair_c.base.symbol,
                                 'decimals': tri.pair_c.base.decimals,
                                 },
                        'quote': {'symbol': tri.pair_c.quote.symbol,
                                  'address': tri.pair_c.quote.symbol,
                                  'decimals': tri.pair_c.quote.decimals,
                                  }
                }}
                for tri in t]))

    async def load_triangules(self):
        try:
            with open('structured_triangules_uniswap.json', 'r') as file:
                self.__triangular_pair_list = [
                    unwrap_triangule(v) for v in json.load(file)]
        except FileNotFoundError:
            print('Arquivo não existe, verificando na corretora')
            await self._get_triangules()
            await self.save_triangular_list()
        else:
            print('Dados Carregados')

    @abstractmethod
    async def _set_pairs(self):
        pass

    @abstractmethod
    async def set_pair_ask_bid(self, info: dict, pair: Pair):
        pass

    async def set_triangular_prices(self, info: list[dict]):
        for t in await self.triangular_pair_list():
            for pair in t.pair_list:
                await self.set_pair_ask_bid(info, pair)

    async def surface_arbitrage(self, triangle: Triangles_pair):
        calculated = 0
        direction_list = ['forward', 'reverse']

        # Poloniex
        # if swapping left (base) to the right (quote)-amount * (1/ask)
        # if swapping right (quote) to the left (base)-amount * bid
        for direction in direction_list:
            if direction == 'forward':
                # assume start a and swap for a_quote
                triangle.swap_1 = triangle.pair_a.base
                triangle.swap_2 = triangle.pair_a.quote
                triangle.swap_1_rate = triangle.pair_a.ask
                triangle.direction_trade_1 = 'base_to_quote'
            else:
                # assume start a and swap for a_base
                triangle.swap_1 = triangle.pair_a.quote
                triangle.swap_2 = triangle.pair_a.base
                triangle.swap_1_rate = triangle.pair_a.bid
                triangle.direction_trade_1 = 'quote_to_base'

            # place_first trade
            triangle.contract_1 = triangle.pair_a
            triangle.acquired_coin_t1 = (
                self.value * triangle.swap_1_rate) * self.fee

            if direction == 'forward':
                # SCENARIO 1 if a_quote macthes b_quote
                if triangle.pair_a.quote.symbol == triangle.pair_b.quote.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_b.bid
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'quote_to_base'
                    triangle.contract_2 = triangle.pair_b

                    # if b_base matches c_base
                    if triangle.pair_b.base.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_c.base
                        triangle.swap_3_rate = triangle.pair_c.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_c

                    # if b_base matches c_quote
                    if triangle.pair_b.base.symbol == triangle.pair_c.quote.symbol:
                        triangle.swap_3 = triangle.pair_c.quote
                        triangle.swap_3_rate = triangle.pair_c.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_c

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

                # SCENARIO 2 if a_quote macthes b_base
                if triangle.pair_a.quote.symbol == triangle.pair_b.base.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_b.ask
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'base_to_quote'
                    triangle.contract_2 = triangle.pair_b

                    # if b_quote matches c_base
                    if triangle.pair_b.quote.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_c.base
                        triangle.swap_3_rate = triangle.pair_c.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_c

                    # if b_quote matches c_quote
                    if triangle.pair_b.quote.symbol == triangle.pair_c.quote.symbol:
                        triangle.swap_3 = triangle.pair_c.quote
                        triangle.swap_3_rate = triangle.pair_c.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_c

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

                # SCENARIO 3 if a_quote macthes c_quote
                if triangle.pair_a.quote.symbol == triangle.pair_c.quote.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_c.bid
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'quote_to_base'
                    triangle.contract_2 = triangle.pair_c

                    # if c_base matches b_base
                    if triangle.pair_b.base.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_b.base
                        triangle.swap_3_rate = triangle.pair_b.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_b

                    # if c_base matches b_quote
                    if triangle.pair_c.base.symbol == triangle.pair_b.quote.symbol:
                        triangle.swap_3 = triangle.pair_b.quote
                        triangle.swap_3_rate = triangle.pair_b.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_b

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

                # SCENARIO 4 if a_quote macthes c_base
                if triangle.pair_a.quote.symbol == triangle.pair_c.base.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_c.ask
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'base_to_quote'
                    triangle.contract_2 = triangle.pair_c

                    # if c_quote matches b_base
                    if triangle.pair_c.quote.symbol == triangle.pair_b.base.symbol:
                        triangle.swap_3 = triangle.pair_b.base
                        triangle.swap_3_rate = triangle.pair_b.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_b

                    # if c_quote matches b_quote
                    if triangle.pair_c.quote.symbol == triangle.pair_b.quote.symbol:
                        triangle.swap_3 = triangle.pair_b.quote
                        triangle.swap_3_rate = triangle.pair_b.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_b

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

            # reverse Scenario
            if direction == 'reverse':
                # SCENARIO 1 if a_base macthes b_quote
                if triangle.pair_a.base.symbol == triangle.pair_b.quote.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_b.bid
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'quote_to_base'
                    triangle.contract_2 = triangle.pair_b

                    # if b_base matches c_base
                    if triangle.pair_b.base.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_c.base
                        triangle.swap_3_rate = triangle.pair_c.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_c

                    # if b_base matches c_quote
                    if triangle.pair_b.base.symbol == triangle.pair_c.quote.symbol:
                        triangle.swap_3 = triangle.pair_c.quote
                        triangle.swap_3_rate = triangle.pair_c.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_c

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

                # SCENARIO 2 if a_base macthes b_base
                if triangle.pair_a.base.symbol == triangle.pair_b.base.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_b.ask
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'base_to_quote'
                    triangle.contract_2 = triangle.pair_b

                    # if b_quote matches c_base
                    if triangle.pair_b.quote.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_c.base
                        triangle.swap_3_rate = triangle.pair_c.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_c

                    # if b_quote matches c_quote
                    if triangle.pair_b.quote.symbol == triangle.pair_c.quote.symbol:
                        triangle.swap_3 = triangle.pair_c.quote
                        triangle.swap_3_rate = triangle.pair_c.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_c

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

                # SCENARIO 3 if a_base macthes c_quote
                if triangle.pair_a.base.symbol == triangle.pair_c.quote.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_c.bid
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'quote_to_base'
                    triangle.contract_2 = triangle.pair_c

                    # if c_base matches b_base
                    if triangle.pair_b.base.symbol == triangle.pair_c.base.symbol:
                        triangle.swap_3 = triangle.pair_b.base
                        triangle.swap_3_rate = triangle.pair_b.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_b

                    # if c_base matches b_quote
                    if triangle.pair_c.base.symbol == triangle.pair_b.quote.symbol:
                        triangle.swap_3 = triangle.pair_b.quote
                        triangle.swap_3_rate = triangle.pair_b.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_b

                    triangle.acquired_coin_t3 = triangle.acquired_coin_t2 * triangle.swap_3_rate
                    calculated = 1

                # SCENARIO 4 if a_base macthes c_base
                if triangle.pair_a.base.symbol == triangle.pair_c.base.symbol and calculated == 0:
                    triangle.swap_2_rate = triangle.pair_c.ask
                    triangle.acquired_coin_t2 = (
                        triangle.acquired_coin_t1 * triangle.swap_2_rate) * self.fee
                    triangle.direction_trade_2 = 'base_to_quote'
                    triangle.contract_2 = triangle.pair_c

                    # if c_quote matches b_base
                    if triangle.pair_c.quote.symbol == triangle.pair_b.base.symbol:
                        triangle.swap_3 = triangle.pair_b.base
                        triangle.swap_3_rate = triangle.pair_b.ask
                        triangle.direction_trade_3 = 'base_to_quote'
                        triangle.contract_3 = triangle.pair_b

                    # if c_quote matches b_quote
                    if triangle.pair_c.quote.symbol == triangle.pair_b.quote.symbol:
                        triangle.swap_3 = triangle.pair_b.quote
                        triangle.swap_3_rate = triangle.pair_b.bid
                        triangle.direction_trade_3 = 'quote_to_base'
                        triangle.contract_3 = triangle.pair_b

                    triangle.acquired_coin_t3 = (
                        triangle.acquired_coin_t2 * triangle.swap_3_rate) * self.fee
                    calculated = 1

            # profit_loss calc
            triangle.profit_loss = triangle.acquired_coin_t3 - self.value
            triangle.profit_loss_perc = (triangle.profit_loss/self.value) * \
                100 if triangle.profit_loss != 0 else 0

            # descriptions
            triangle.trade_description_1 = f'Start with {triangle.swap_1.symbol} of {self.value} - '
            triangle.trade_description_1 += f'Swap at {triangle.swap_1_rate} for {triangle.swap_2.symbol} acquiring {triangle.acquired_coin_t1}'
            triangle.trade_description_2 = f'Swap {triangle.acquired_coin_t1} of {triangle.swap_2.symbol} '
            triangle.trade_description_2 += f'at {triangle.swap_2_rate} for {triangle.swap_3.symbol} acquiring {triangle.acquired_coin_t2}'
            triangle.trade_description_3 = f'Swap {triangle.acquired_coin_t2} of {triangle.swap_3.symbol} '
            triangle.trade_description_3 += f'at {triangle.swap_3_rate} for {triangle.swap_1.symbol} acquiring {triangle.acquired_coin_t3}'
            triangle.direction = direction
            if triangle.profit_loss_perc > self.min_surface_rate:
                return triangle
        return

    async def _calc_surface(self):
        result = await asyncio.gather(*[asyncio.create_task(self.surface_arbitrage(tri)) for tri in await self.triangular_pair_list()])
        return result

    async def describe_triangle(self, triangle: Triangles_pair) -> None:
        if triangle:
            print('\n', triangle.combined)
            print(triangle.direction)
            print(triangle.trade_description_1)
            print(triangle.trade_description_2)
            print(triangle.trade_description_3)
            print(f'Amount out{triangle.profit_loss}')
            print(f'Percentage of Gain {triangle.profit_loss_perc}\n')
