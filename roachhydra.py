# goal is push with roach/hydra A move 

from functools import reduce
from operator import or_
import random

import sc2
from sc2 import Race, Difficulty, run_game
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.data import race_townhalls

import enum


class RoachHydra(sc2.BotAI):
	def __init__(self):
		self.ITERATIONS_PER_MINUTE = 165		
		self.drone_counter = 0

	async def on_step(self, iteration):
		await self.distribute_workers()
		await self.expand()
		await self.build_extractor()
		await self.offensivebuildings()
		await self.buildarmy()
		await self.buildworkers()
		await self.createoverlords()
		await self.injectlarva()
		await self.attack()
		await self.buyupgrades()


	def find_target(self, state):
		if len(self.known_enemy_units) > 0:
			return random.choice(self.known_enemy_units)
		elif len(self.known_enemy_structures) > 0:
			return random.choice(self.known_enemy_structures)
		else:
			return self.enemy_start_locations[0]

	async def attack(self):
		aggressive_units = {ROACH: [13,5],
							HYDRALISK: [10,5]}
		for UNIT in aggressive_units:
			if self.units(UNIT).amount > aggressive_units[UNIT][0] and self.units(UNIT).amount > aggressive_units[UNIT][1]:
				for s in self.units(UNIT).idle:
					await self.do(s.attack(self.find_target(self.state)))

			elif self.units(UNIT).amount > aggressive_units[UNIT][1]:
				if len(self.known_enemy_units) > 0:
					for s in self.units(UNIT).idle:
						await self.do(s.attack(random.choice(self.known_enemy_units)))

	async def buyupgrades(self):
		if self.units(ROACHWARREN).ready.idle.amount > 0 and self.units(ROACH).amount > 10:
			rw = self.units(ROACHWARREN).ready.idle.random
			abilities = await self.get_available_abilities(rw)
			if AbilityId.RESEARCH_GLIALREGENERATION in abilities and self.can_afford(AbilityId.RESEARCH_GLIALREGENERATION):
				error = await self.do(rw(AbilityId.RESEARCH_GLIALREGENERATION))

		if self.units(HYDRALISKDEN).ready.idle.amount > 0 and self.units(HYDRALISK).amount > 10:
			rw = self.units(HYDRALISKDEN).ready.idle.random
			abilities = await self.get_available_abilities(rw)
			if AbilityId.RESEARCH_MUSCULARAUGMENTS in abilities and self.can_afford(AbilityId.RESEARCH_MUSCULARAUGMENTS):
				error = await self.do(rw(AbilityId.RESEARCH_MUSCULARAUGMENTS))
			if AbilityId.RESEARCH_GROOVEDSPINES in abilities and self.can_afford(AbilityId.RESEARCH_GROOVEDSPINES):
				error = await self.do(rw(AbilityId.RESEARCH_GROOVEDSPINES))

		if self.units(EVOLUTIONCHAMBER).ready.idle.exists and self.units(ROACH).amount > 10:
			for evo in self.units(EVOLUTIONCHAMBER).ready.idle:
				abilities = await self.get_available_abilities(evo)
				targetAbilities = [AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL1, AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL2, AbilityId.RESEARCH_ZERGMISSILEWEAPONSLEVEL3, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL1, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL2, AbilityId.RESEARCH_ZERGGROUNDARMORLEVEL3]
				if self.units(GREATERSPIRE).exists:
					targetAbilities.extend([AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL1,
					AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL2,
					AbilityId.RESEARCH_ZERGMELEEWEAPONSLEVEL3])
				for ability in targetAbilities:
					if ability in abilities:
						if self.can_afford(ability):
							err = await self.do(evo(ability))
							if not err:
								break




	async def injectlarva(self):
		if not self.townhalls.exists:
			for unit in self.units(DRONE) | self.units(QUEEN) | forces:
				await self.do(unit.attack(self.enemy_start_locations[0]))
				return
		else: 
			hq = self.townhalls.first



		for queen in self.units(QUEEN).idle: #injects larva 
			abilities = await self.get_available_abilities(queen)
			if AbilityId.EFFECT_INJECTLARVA in abilities:
				await self.do(queen(EFFECT_INJECTLARVA, hq))



		if self.units(SPAWNINGPOOL).ready.exists: #creates queens
			if not self.units(QUEEN).exists and hq.is_ready and hq.noqueue:
				if self.can_afford(QUEEN):
					await self.do(hq.train(QUEEN))




	async def createoverlords(self):
			larvae = self.units(LARVA)
			if self.supply_left < 2: #create overlords
				if self.can_afford(OVERLORD) and larvae.exists:
					await self.do(larvae.random.train(OVERLORD))
			

	async def buildworkers(self):
		larvae = self.units(LARVA)
		if self.drone_counter < 70: #create workers
			if self.can_afford(DRONE) and larvae.exists:
				self.drone_counter += 1
				await self.do(larvae.random.train(DRONE))

	async def buildarmy(self):
		larvae = self.units(LARVA)
		forces = self.units(ZERGLING) | self.units(HYDRALISK) | self.units(ROACH)
		if self.units(ZERGLING).amount < 20 and self.minerals > 500:
			if larvae.exists and self.can_afford(ZERGLING):
				await self.do(larvae.random.train(ZERGLING))
				return

		if self.units(ROACHWARREN).ready.exists:
			if self.can_afford(ROACH) and larvae.exists:
				if not self.units(ROACH).amount > self.units(HYDRALISK).amount:
					await self.do(larvae.random.train(ROACH))
					return

		if self.units(HYDRALISKDEN).ready.exists:
			if self.can_afford(HYDRALISK) and larvae.exists:
				await self.do(larvae.random.train(HYDRALISK))
				return




	async def offensivebuildings(self):
		hq = self.townhalls.first
		if not (self.units(SPAWNINGPOOL).exists or self.already_pending(SPAWNINGPOOL)): #creates spawning pool
			if self.can_afford(SPAWNINGPOOL):
				await self.build(SPAWNINGPOOL, near=hq)

		if self.units(SPAWNINGPOOL).ready.exists:
			if not (self.units(ROACHWARREN).exists or self.already_pending(ROACHWARREN)):
				if self.can_afford(ROACHWARREN):
					await self.build(ROACHWARREN, near=hq)

		if self.units(ROACHWARREN).ready.exists and self.already_pending(LAIR) < 1:
			if not self.units(LAIR).exists and hq.noqueue:
				if self.can_afford(LAIR):
					await self.do(hq.build(LAIR))

		if self.units(LAIR).ready.exists:
			if not (self.units(HYDRALISKDEN).exists or self.already_pending(HYDRALISKDEN)):
				if self.can_afford(HYDRALISKDEN):
					await self.build(HYDRALISKDEN, near=hq)

		if self.units(ROACHWARREN).ready.exists:
			if not (self.units(EVOLUTIONCHAMBER).exists or self.already_pending(EVOLUTIONCHAMBER)):
				if self.can_afford(EVOLUTIONCHAMBER):
					await self.build(EVOLUTIONCHAMBER, near=hq)
					






	async def expand(self): #expands to new hatchery
		if self.units(HATCHERY).amount < 3 and self.can_afford(HATCHERY):
			await self.expand_now() 

	async def build_extractor(self): #builds extractors for gas
		for hatchery in self.units(HATCHERY).ready:
			vaspenes = self.state.vespene_geyser.closer_than(15.0, hatchery)
			for vaspene in vaspenes:
				if not self.can_afford(EXTRACTOR):
					break

				if not self.units(EXTRACTOR).closer_than(1.0, vaspene).exists:
					if self.can_afford(EXTRACTOR):
						drone = self.workers.random
						target = self.state.vespene_geyser.closest_to(drone.position)
						err = await self.do(drone.build(EXTRACTOR, target))

run_game(sc2.maps.get("AcropolisLE"), [
	Bot(Race.Zerg, RoachHydra()),
	Computer(Race.Protoss, Difficulty.Medium)
	], realtime=False)