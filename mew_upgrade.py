
from sharpy.plans.acts import ActBase, Tech, MorphWarpGates, GridBuilding
from sharpy.plans.acts.morph_building import MorphBuilding
from sharpy.plans import BuildOrder, SequentialList, Step
from sharpy.plans.require import UnitReady, TechReady, UnitExists, Any, All
from sc2.constants import UpgradeId, UnitTypeId


class ZergUpgrades:
    upgrade_zerg_ground_armor= SequentialList(
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGGROUNDARMORSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.ZERGGROUNDARMORSLEVEL1, 1)
        )),
        Step(None,Tech(UpgradeId.ZERGGROUNDARMORSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.HIVE, 1),
              TechReady(UpgradeId.ZERGGROUNDARMORSLEVEL2, 1)
        )),
    )

    upgrade_zerg_ground_melee= SequentialList(
        Step(None, Tech(UpgradeId.ZERGMELEEWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGMELEEWEAPONSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.ZERGMELEEWEAPONSLEVEL1, 1)
        )),
        Step(None,
           Tech(UpgradeId.ZERGMELEEWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.HIVE, 1),
              TechReady(UpgradeId.ZERGMELEEWEAPONSLEVEL2, 1)
        )),
    )
    upgrade_zerg_ground_ranged= SequentialList(
        Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.ZERGMISSILEWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.ZERGMISSILEWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.HIVE, 1),
              TechReady(UpgradeId.ZERGMISSILEWEAPONSLEVEL2, 1)
        )),
    )

    upgrade_zerg_air_attack= SequentialList(
        Step(None, Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.ZERGFLYERWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.HIVE, 1),
              TechReady(UpgradeId.ZERGFLYERWEAPONSLEVEL2, 1)
        )),
    )

    upgrade_zerg_air_armor= SequentialList(
        Step(None, Tech(UpgradeId.ZERGFLYERARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.ZERGFLYERARMORSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.ZERGFLYERARMORSLEVEL2, 1)
        )),
        Step(None, Tech(UpgradeId.ZERGFLYERARMORSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.HIVE, 1),
              TechReady(UpgradeId.ZERGFLYERARMORSLEVEL2, 1)
        )),
    )

    ling_upgrades = BuildOrder([
        Step(None, Tech(UpgradeId.ZERGLINGMOVEMENTSPEED), skip_until=UnitReady(UnitTypeId.SPAWNINGPOOL, 1)), # ling speed
        Step(None, Tech(UpgradeId.ZERGLINGATTACKSPEED), skip_until=All(UnitReady(UnitTypeId.SPAWNINGPOOL, 1), UnitExists(UnitTypeId.HIVE, 1))), # ling crack
        Step(None , Tech(UpgradeId.CENTRIFICALHOOKS), skip_until=All(UnitReady(UnitTypeId.SPAWNINGPOOL, 1), UnitExists(UnitTypeId.LAIR, 1))), # bane speed
        ])

    roach_upgrades = BuildOrder([
        Step(UnitExists(UnitTypeId.LAIR, 1), Tech(UpgradeId.GLIALRECONSTITUTION), skip_until=UnitReady(UnitTypeId.ROACHWARREN, 1)), # roach speed
        Step(UnitExists(UnitTypeId.LAIR, 1), Tech(UpgradeId.TUNNELINGCLAWS), skip_until=TechReady(UpgradeId.BURROW, 1)), # roach burrow move
        ])

    hydra_upgrades = SequentialList([
        Step(None, Tech(UpgradeId.EVOLVEMUSCULARAUGMENTS), skip_until=UnitReady(UnitTypeId.HYDRALISKDEN, 1)), # hydra speed
        Step(None, Tech(UpgradeId.EVOLVEGROOVEDSPINES), skip_until=UnitReady(UnitTypeId.HYDRALISKDEN, 1)), # hydra range
        
        ])
    lurker_upgrades = SequentialList([
        Step(UnitExists(UnitTypeId.HIVE, 1), Tech(UpgradeId.LURKERRANGE), skip_until=UnitReady(UnitTypeId.LURKERDENMP, 1)), # lurker range
        Step(UnitExists(UnitTypeId.HIVE, 1), Tech(UpgradeId.DIGGINGCLAWS), skip_until=UnitReady(UnitTypeId.LURKERDENMP, 1)), #lurker burrow speed
        
        ])


    ultra_upgrades = BuildOrder([
        Step(None, Tech(UpgradeId.CHITINOUSPLATING), skip_until=UnitReady(UnitTypeId.ULTRALISKCAVERN, 1)), # ultra armor
        Step(None, Tech(UpgradeId.ANABOLICSYNTHESIS), skip_until=UnitReady(UnitTypeId.ULTRALISKCAVERN, 1)), # ultra speed
        ])

class HandleZergUpgrades(BuildOrder):
    
    def __init__(self):
        self.armor= Step(UnitReady(UnitTypeId.EVOLUTIONCHAMBER, 1), ZergUpgrades.upgrade_zerg_ground_armor)
        self.melee= Step(UnitReady(UnitTypeId.EVOLUTIONCHAMBER, 1), ZergUpgrades.upgrade_zerg_ground_melee)
        self.ranged= Step(UnitReady(UnitTypeId.EVOLUTIONCHAMBER, 1), ZergUpgrades.upgrade_zerg_ground_ranged)

        self.air_attack = Step(Any(UnitReady(UnitTypeId.SPIRE, 1),UnitReady(UnitTypeId.GREATERSPIRE, 1)), ZergUpgrades.upgrade_zerg_air_attack)
        self.air_armor = Step(Any(UnitReady(UnitTypeId.SPIRE, 1),UnitReady(UnitTypeId.GREATERSPIRE, 1)), ZergUpgrades.upgrade_zerg_air_armor)


        my_orders = [
            
            ZergUpgrades.ling_upgrades,
            ZergUpgrades.roach_upgrades,
            ZergUpgrades.hydra_upgrades,
            ZergUpgrades.lurker_upgrades,
            ZergUpgrades.ultra_upgrades,

            

            #air upgrades
            BuildOrder(self.air_attack, self.air_armor),
            
            #ground upgrades
            BuildOrder(self.armor, self.ranged, self.melee ), 

            Step(None, Tech(UpgradeId.NEURALPARASITE), skip_until=UnitReady(UnitTypeId.INFESTATIONPIT, 1)), # neural parasite

            Step(UnitExists(UnitTypeId.LAIR, 1, include_pending=True), Tech(UpgradeId.BURROW), skip_until=UnitReady(UnitTypeId.ROACHWARREN, 1)), # burrow
            Step(None, Tech(UpgradeId.OVERLORDSPEED), skip_until=UnitReady(UnitTypeId.LAIR, 1)), # overlord speed

            
        ]
        super().__init__(my_orders)


    async def execute(self) -> bool: 

        return await super().execute()

class ProtossUpgrades:
    upgrade_protoss_ground_attack= SequentialList(
        Step(None, Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.CYBERNETICSCORE, 1),
              TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
              TechReady(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, 1)
        ))
    )

    upgrade_protoss_shields= SequentialList(
        Step(None, Tech(UpgradeId.PROTOSSSHIELDSLEVEL1)),
        Step(None, Tech(UpgradeId.PROTOSSSHIELDSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.CYBERNETICSCORE, 1),
              TechReady(UpgradeId.PROTOSSSHIELDSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.PROTOSSSHIELDSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
              TechReady(UpgradeId.PROTOSSSHIELDSLEVEL2, 1)
        )),
    )
    upgrade_protoss_ground_armor= SequentialList(
        Step(None, Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.CYBERNETICSCORE, 1),
              TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.PROTOSSGROUNDARMORSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1),
              TechReady(UpgradeId.PROTOSSGROUNDARMORSLEVEL2, 1)
        )),
    )
    upgrade_protoss_air_attack= SequentialList(
        Step(None, Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.PROTOSSAIRWEAPONSLEVEL2),
           skip_until=All(
              #UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.ZERGFLYERWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.FLEETBEACON, 1),
              TechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL2, 1)
        )),
    )
    upgrade_protoss_air_armor= SequentialList(
        Step(None, Tech(UpgradeId.PROTOSSAIRARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.PROTOSSAIRARMORSLEVEL2),
           skip_until=All(
              #UnitReady(UnitTypeId.LAIR, 1),
              TechReady(UpgradeId.PROTOSSAIRARMORSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.PROTOSSAIRARMORSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.FLEETBEACON, 1),
              TechReady(UpgradeId.PROTOSSAIRARMORSLEVEL2, 1)
        )),
    )

class HandleProtossUpgrades(BuildOrder):
    
    def __init__(self):
        self.weapon= Step(UnitReady(UnitTypeId.FORGE, 1), ProtossUpgrades.upgrade_protoss_ground_attack)
        self.shield= Step(UnitReady(UnitTypeId.FORGE, 1), ProtossUpgrades.upgrade_protoss_shields)
        self.armor= Step(UnitReady(UnitTypeId.FORGE, 1), ProtossUpgrades.upgrade_protoss_ground_armor)


        self.air_attack = Step(All(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), UnitExists(UnitTypeId.STARGATE, 2)), ProtossUpgrades.upgrade_protoss_air_attack)
        self.air_armor = Step(All(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), UnitExists(UnitTypeId.STARGATE, 2)), ProtossUpgrades.upgrade_protoss_air_armor)


        my_orders = [
            
            Step(UnitReady(UnitTypeId.FLEETBEACON, 1), Tech(UpgradeId.VOIDRAYSPEEDUPGRADE)), # voidray speed

            Step(UnitReady(UnitTypeId.FLEETBEACON, 1), Tech(UpgradeId.TEMPESTGROUNDATTACKUPGRADE)), # tempest attack

            Step(UnitReady(UnitTypeId.ROBOTICSBAY, 1), Tech(UpgradeId.EXTENDEDTHERMALLANCE)), # colossus range
            Step(UnitReady(UnitTypeId.CYBERNETICSCORE, 1), Tech(UpgradeId.WARPGATERESEARCH)), # warp gate
            
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.CHARGE)), # zealot speed
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.BLINKTECH)),
            Step(UnitReady(UnitTypeId.TWILIGHTCOUNCIL, 1), Tech(UpgradeId.ADEPTPIERCINGATTACK)),
            Step(UnitReady(UnitTypeId.TEMPLARARCHIVE, 1), Tech(UpgradeId.PSISTORMTECH)), # psi storm
            
            Step(TechReady(UpgradeId.WARPGATERESEARCH, 1), MorphWarpGates()), # warp gate
            #air upgrades
            Step(TechReady(UpgradeId.WARPGATERESEARCH, 1), BuildOrder(self.air_attack, self.air_armor)), 
            #ground upgrades
            Step(TechReady(UpgradeId.WARPGATERESEARCH, 1), BuildOrder(self.weapon, self.armor,self.shield)), 

            
            Step(UnitExists(UnitTypeId.ROBOTICSFACILITY, 1), GridBuilding(UnitTypeId.ROBOTICSBAY,1, priority=True)),
            Step(All(UnitExists(UnitTypeId.STARGATE, 1), TechReady(UpgradeId.PROTOSSAIRWEAPONSLEVEL1, 0.23)), GridBuilding(UnitTypeId.FLEETBEACON,1, priority=True))
            #Step(TechReady(UpgradeId.WARPGATERESEARCH, 0.75), ChronoTech(UpgradeId.WARPGATERESEARCH, UnitTypeId.CYBERNETICSCORE)),
            
            
            
            
        ]
        super().__init__(my_orders)


    async def execute(self) -> bool: 

        return await super().execute()

class TerranUpgrades:
    upgrade_terran_infantry_attack= SequentialList(
        Step(None, Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2),
           skip_until=All(
              UnitExists(UnitTypeId.ARMORY, 1),
              UnitReady(UnitTypeId.ENGINEERINGBAY, 1),
              TechReady(UpgradeId.TERRANINFANTRYWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.TERRANINFANTRYWEAPONSLEVEL3),
           skip_until=All(
              UnitExists(UnitTypeId.ARMORY, 1),
              UnitReady(UnitTypeId.ENGINEERINGBAY, 1),
              TechReady(UpgradeId.TERRANINFANTRYWEAPONSLEVEL2, 1)
        ))
    )

    upgrade_terran_infantry_armor= SequentialList(
        Step(None, Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL2),
           skip_until=All(
              UnitExists(UnitTypeId.ARMORY, 1),
              UnitReady(UnitTypeId.ENGINEERINGBAY, 1),
              TechReady(UpgradeId.TERRANINFANTRYARMORSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.TERRANINFANTRYARMORSLEVEL3),
           skip_until=All(
              UnitExists(UnitTypeId.ARMORY, 1),
              UnitReady(UnitTypeId.ENGINEERINGBAY, 1),
              TechReady(UpgradeId.TERRANINFANTRYARMORSLEVEL2, 1)
        )),
    )
    upgrade_terran_vehicle_armor= SequentialList(
        Step(None, Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1)),
        Step(None, Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.ARMORY, 1),
              TechReady(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.ARMORY, 1),
              TechReady(UpgradeId.TERRANVEHICLEANDSHIPARMORSLEVEL2, 1)
        )),
    )
    upgrade_terran_vehicle_weapons= SequentialList(
        Step(None, Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1)),
        Step(None, Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2),
           skip_until=All(
              UnitReady(UnitTypeId.ARMORY, 1),
              TechReady(UpgradeId.TERRANVEHICLEWEAPONSLEVEL1, 1)
        )),
        Step(None, Tech(UpgradeId.TERRANVEHICLEWEAPONSLEVEL3),
           skip_until=All(
              UnitReady(UnitTypeId.ARMORY, 1),
              TechReady(UpgradeId.TERRANVEHICLEWEAPONSLEVEL2, 1)
        )),
    )
    infantry_upgrades = BuildOrder([
        Step(UnitReady(UnitTypeId.BARRACKSTECHLAB, 1) , Tech(UpgradeId.SHIELDWALL),), # marine shield
        Step(UnitReady(UnitTypeId.BARRACKSTECHLAB, 1), Tech(UpgradeId.STIMPACK)), # stim
        Step(UnitReady(UnitTypeId.BARRACKSTECHLAB, 1), Tech(UpgradeId.PUNISHERGRENADES),), #concussive shells
        Step(UnitReady(UnitTypeId.GHOSTACADEMY, 1), Tech(UpgradeId.PERSONALCLOAKING),), #ghost cloak
        
        ])
    mech_upgrades = BuildOrder([
        Step(UnitReady(UnitTypeId.FACTORYTECHLAB, 1) , Tech(UpgradeId.HIGHCAPACITYBARRELS)), #hellion attack
        #Step(None , Tech(UpgradeId.CYCLONELOCKONDAMAGEUPGRADE), skip_until=UnitReady(UnitTypeId.FACTORYTECHLAB, 1)), #cyclone attack
        Step(UnitReady(UnitTypeId.FACTORYTECHLAB, 1), Tech(UpgradeId.SMARTSERVOS)), #smart servos
        ])
    banshee_upgrades = BuildOrder([
        Step(None , Tech(UpgradeId.BANSHEECLOAK), skip_until=UnitReady(UnitTypeId.STARPORTTECHLAB, 1)), #banshee cloak attack
        Step(None , Tech(UpgradeId.BANSHEESPEED), skip_until=UnitReady(UnitTypeId.STARPORTTECHLAB, 1)), #banshee speed
        ])
    battlecruiser_upgrades = BuildOrder([
        Step(None, Tech(UpgradeId.BATTLECRUISERENABLESPECIALIZATIONS), skip_until=All(UnitReady(UnitTypeId.FUSIONCORE, 1))), #yamato cannon
        ])

class HandleTerranUpgrades(BuildOrder):
    
    def __init__(self):
        self.infantry_attack= Step(UnitReady(UnitTypeId.ENGINEERINGBAY, 1), TerranUpgrades.upgrade_terran_infantry_attack)
        self.infantry_armor= Step(UnitReady(UnitTypeId.ENGINEERINGBAY, 1), TerranUpgrades.upgrade_terran_infantry_armor)
        self.mech_armor = Step(UnitReady(UnitTypeId.ARMORY, 1), TerranUpgrades.upgrade_terran_vehicle_armor)
        self.mech_attack = Step(UnitReady(UnitTypeId.ARMORY, 1), TerranUpgrades.upgrade_terran_vehicle_weapons)
        my_orders = [
            #ground upgrades
            BuildOrder(self.infantry_attack, self.infantry_armor, self.mech_attack, self.mech_armor),
            BuildOrder(TerranUpgrades.infantry_upgrades, TerranUpgrades.mech_upgrades, TerranUpgrades.battlecruiser_upgrades),
            

        ]
        super().__init__(my_orders)

    async def execute(self) -> bool: 

        return await super().execute()