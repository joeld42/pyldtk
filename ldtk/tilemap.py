from enum import Enum

import os, sys
import json

# ===============================================
#  Enums
# ===============================================
class WorldLayout( str, Enum ):
    Freeform = 'Free'
    GridVania = 'GridVania'
    LinearHorizontal = 'LinearHorizontal'
    LinearVertical = 'LinearVertical'

class LayerType( str, Enum ):
    IntGrid = 'IntGrid'
    Entities = 'Entities'
    Tiles = 'Tiles'
    AutoLayer = 'AutoLayer'

class FlipBits( int, Enum ):
    FlipNone = 0
    FlipX = 1
    FlipY = 2
    FlipXY = 3

# ===============================================
#  TilesetDef
# ===============================================
class TilesetDef( object ):
    def __init__(self):

        self.identifier = "Unnamed Tileset"
        self.relPath = "image_missing.png"
        self.uid = "ERR"
        self.size = (0, 0)
        self.tileGridSize = 16
        self.spacing = 0
        self.padding = 0

    @staticmethod
    def from_dict(data):

        tileset = TilesetDef()
        tileset.uid = data.get('uid')
        tileset.identifier = data.get( 'identifier', "Unnamed Tileset")
        tileset.relPath = data.get( 'relPath', tileset.relPath )
        tileset.tileGridSize = data.get( 'tileGridSize', tileset.tileGridSize )

        szx = int(data.get('pxWid'))
        szy = int(data.get('pxHei'))
        tileset.size = (szx, szy)
        tileset.spacing = int(data.get('spacing'))
        tileset.padding = int(data.get('padding'))

        return tileset

# ===============================================
#  Tile Layer Def
# ===============================================
class TileLayerDef( object ):
    def __init__(self):

        self.identifier = "Unnamed Layer"
        self.uid = "ERR"
        self.gridSize = 16
        self.layerType = LayerType.Tiles
        self.tilesetDefUID = "???"

    @staticmethod
    def from_dict( data ):

        layerDef = TileLayerDef()
        layerDef.identifier = data.get( 'identifier', layerDef.identifier )
        layerDef.uid = data.get( 'uid', layerDef.uid )
        layerDef.layerType = data.get( '__type', layerDef.layerType )
        layerDef.tilesetDefUID = data.get( 'tilesetDefUid', layerDef.tilesetDefUID )

        return layerDef

# ===============================================
#  TileLayer (Instance)
# ===============================================
class TileLayer( object ):
    def __init__(self):

        self.iid = 'ERR'

        self.tiles = []
        self.entities = []
        self.intGridData = None
        self.layerDefUid = '???'
        self.levelId = '???'
        self.overrideTilesetUid = None
        self.pxOffset = (0, 0)
        self.visible = True

    @staticmethod
    def from_dict( data ):

        layer = TileLayer()
        layer.iid = data.get('iid')
        layer.layerDefUid = data.get('layerDefUid')

        if layer.layerDefUid is None:
            print("NO Layerdef Uid!", data.keys() )
            sys.exit(1)

        layer.levelId = data.get( 'levelId' )
        layer.overrideTilesetUid = data.get('overrideTilesetUid')

        pxOffsetX = data.get( 'pxOffsetX', 0 )
        pxOffsetY = data.get( 'pxOffsetY', 0)
        layer.pxOffset = (pxOffsetX, pxOffsetY )

        layer.visible = data.get('visible', layer.visible )

        # Look at layer type to see which data to read
        layerType = data.get('__type')
        if layerType == LayerType.IntGrid:
            layer.intGridData = data.get( 'intGridCsv')
            # Int layers may have tiles
            layer.tiles = TileLayer.tiles_from_data(data.get('autoLayerTiles'))
        elif layerType == LayerType.Tiles:
            layer.tiles = TileLayer.tiles_from_data( data.get( 'gridTiles') )
        elif layerType == LayerType.AutoLayer:
            layer.tiles = TileLayer.tiles_from_data(data.get('autoLayerTiles'))
        elif layerType == LayerType.Entities:
            layer.entities = TileLayer.entities_from_data( data.get('entityInstances'))

        return layer

    @staticmethod
    def entities_from_data( entityData ):
        # TODO: read entities
        return []

    @staticmethod
    def tiles_from_data( tileData ):
        tiles = []

        for td in tileData:
            t = Tile.from_data( td )
            tiles.append( t )

        return tiles

# ===============================================
#  Tile
# ===============================================
class Tile( object ):
    def __init__(self):
        self.flip = FlipBits.FlipNone
        self.pxy = ( 0, 0 )
        self.src = ( 0, 0 )
        self.t = -1

    @staticmethod
    def from_data( data ):
        tile = Tile()
        tile.flip = data.get( 'f', FlipBits.FlipNone )
        tile.pxy = tuple(data.get('px'))
        tile.src = tuple( data.get( 'src'))
        tile.t = data.get( 't' )
        return tile


# ===============================================
#  TileLevel
# ===============================================
class TileLevel( object ):
    def __init__(self):

        self.identifier = "Unnamed"
        self.worldPos = ( 0, 0 )
        self.worldDepth = 0
        self.size = ( 0, 0)
        self.layers = []
        self.collision = []
        self.tiles = []

    @staticmethod
    def from_dict( data ):

        level = TileLevel()
        level.identifier = data.get( 'identifier', "Unnamed" )
        wx = int(data.get('worldX'))
        wy = int(data.get('worldY'))
        wd = int(data.get('worldDepth'))
        level.worldPos = ( wx, wy )
        level.worldDepth = wd

        szx = int(data.get('pxWid'))
        szy = int(data.get('pxHei'))
        level.size = (szx, szy )

        # LDTK saves layerInstances front-to-back, but we want them
        # back-to-front
        layerInsts = list(data.get('layerInstances', []))
        layerInsts.reverse()
        for layerData in layerInsts:
            layer = TileLayer.from_dict( layerData )
            level.layers.append( layer )

        return level

# ===============================================
#  TileWorld
# ===============================================
class TileWorld( object ):

    def __init__(self):
        self.gridSize = (1, 1)  # only for Gridvania style
        self.layout = WorldLayout.Freeform

    @staticmethod
    def from_dict( data ):
        world = TileWorld()
        gridWidth = data.get("worldGridWidth", world.gridSize[0])
        gridHeight = data.get("worldGridHeight", world.gridSize[1])
        world.gridSize = (gridWidth, gridHeight)
        world.layout = data.get("worldLayout", world.layout)

        return world

# ===============================================
#  TileProject
# ===============================================
class TileProject( object ):

    def __init__( self ):

        self.world = TileWorld()
        self.levels = []
        self.tilesetDefs = {}
        self.layerDefs = {}

        self.externalLevels = False

    def layerDefForLayer(self, layer ):
        return self.layerDefs[ layer.layerDefUid ]

    def layerTypeForLayer(self, layer ):
        layerDef = self.layerDefs[ layer.layerDefUid ]
        return layerDef.layerType

    def doesLayerContainTileData(self, layer ):
        layerType = self.layerTypeForLayer( layer )
        return (layerType != LayerType.Entities)

    @staticmethod
    def from_dict( data ):

        proj = TileProject()

        # World values
        # For now this is using the old format, with one world in the
        # project root, but i'm putting the world data in World to make things easy to change
        # in the "multiple worlds update"
        proj.world = TileWorld.from_dict( data )

        # Check the external levels flag even though we're not using it yet
        proj.externalLevels = data.get( 'externalLevels', proj.externalLevels )
        if proj.externalLevels:
            print("WARNING: External levels set to True. External level files are not supported yet in the importer, so this will probably break.")

        # Parse defs
        defs = data.get('defs', {} )

        # Read tileset defs
        for tilesetDefData in defs.get('tilesets', []):
            tilesetDef = TilesetDef.from_dict( tilesetDefData )

            proj.tilesetDefs[ tilesetDef.uid ] = tilesetDef

        # Read layer defs
        for layerDefData in defs.get('layers', []):
            layerDef = TileLayerDef.from_dict( layerDefData )

            proj.layerDefs[layerDef.uid ] = layerDef

        # Parse levels
        for leveldata in data.get('levels', []):
            level = TileLevel.from_dict( leveldata )
            proj.levels.append( level )

        return proj

