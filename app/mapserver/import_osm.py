import osmium
import sqlite3

DB = "places.db"
PBF_FILE = "/data/us-northeast-latest.osm.pbf"

conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode = WAL")
conn.execute("PRAGMA synchronous = NORMAL")
conn.execute("PRAGMA temp_store = MEMORY")
conn.execute("PRAGMA cache_size = -200000")

# Prepare UPSERT statement once
UPSERT_SQL = """
INSERT INTO places 
(osm_type, osm_id, name, lat, lon, type, address, city, state, postcode, geohash, is_address, is_emergency, emergency_type, osm_tags)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(osm_type, osm_id) DO UPDATE SET
    name=excluded.name,
    lat=excluded.lat,
    lon=excluded.lon,
    type=excluded.type,
    address=excluded.address,
    city=excluded.city,
    state=excluded.state,
    postcode=excluded.postcode,
    geohash=excluded.geohash,
    is_address=excluded.is_address,
    is_emergency=excluded.is_emergency,
    emergency_type=excluded.emergency_type,
    osm_tags=excluded.osm_tags
"""

# Create table with all columns (indexes created AFTER import for speed)
conn.execute("""
CREATE TABLE IF NOT EXISTS places (
    id INTEGER PRIMARY KEY,
    osm_type TEXT,
    osm_id INTEGER,
    name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    type TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    postcode TEXT,
    geohash TEXT,
    is_address BOOLEAN DEFAULT 0,
    is_emergency BOOLEAN DEFAULT 0,
    emergency_type TEXT,
    osm_tags TEXT,
    UNIQUE(osm_type, osm_id)
)
""")
conn.commit()

# New Hampshire bounding box
NH_BBOX = (42.7, 45.3, -72.6, -70.7)

def is_in_nh(lat, lon):
    """Check if coordinates are in New Hampshire"""
    return (NH_BBOX[0] <= lat <= NH_BBOX[1] and 
            NH_BBOX[2] <= lon <= NH_BBOX[3])

def geohash_encode(lat, lon, precision=7):
    """Encode lat/lon to geohash"""
    lat_range = [-90.0, 90.0]
    lon_range = [-180.0, 180.0]
    geohash = []
    bits = 0
    bit = 0
    ch = 0
    
    base32 = "0123456789bcdefghjkmnpqrstuvwxyz"
    
    while len(geohash) < precision:
        if bits % 2 == 0:
            mid = (lon_range[0] + lon_range[1]) / 2
            if lon > mid:
                ch |= (1 << (4 - bit))
                lon_range[0] = mid
            else:
                lon_range[1] = mid
        else:
            mid = (lat_range[0] + lat_range[1]) / 2
            if lat > mid:
                ch |= (1 << (4 - bit))
                lat_range[0] = mid
            else:
                lat_range[1] = mid
        
        bits += 1
        if bits % 5 == 0:
            geohash.append(base32[ch])
            ch = 0
        
        bit += 1
        if bit == 5:
            bit = 0
    
    return ''.join(geohash)

def is_emergency_type(tags):
    """Check if location is an emergency service"""
    emergency_amenities = {
        'hospital': 'hospital',
        'fire_station': 'fire_station',
        'police': 'police',
        'pharmacy': 'pharmacy',
        'ambulance_station': 'ambulance_station',
    }
    
    if 'amenity' in tags and tags['amenity'] in emergency_amenities:
        return True, emergency_amenities[tags['amenity']]
    
    if tags.get('emergency') == 'yes':
        return True, 'emergency'
    
    return False, None

def tags_to_json(tags):
    """Convert OSM tags dict to JSON string"""
    import json
    # Store useful emergency/POI info
    useful_keys = [
        'name', 'amenity', 'shop', 'type', 'operator', 'phone', 'website',
        'opening_hours', 'wheelchair', 'capacity', 'emergency', 'building',
        'addr:street', 'addr:housenumber', 'addr:city', 'addr:state', 'addr:postcode'
    ]
    
    filtered_tags = {k: tags[k] for k in useful_keys if k in tags}
    return json.dumps(filtered_tags)

def detect_place_type(tags):
    """Detect place type from OSM tags, returning key:value for better filtering"""
    priority = [
        "amenity",
        "shop",
        "tourism",
        "office",
        "craft",
        "leisure",
        "historic",
        "place",
        "natural",
        "railway",
        "highway",
        "building",
    ]

    for key in priority:
        value = tags.get(key)
        if value:
            return f"{key}:{value}"

    return None

class PlaceHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.count = 0
    
    def maybe_commit(self):
        """Commit and checkpoint every 50k rows"""
        if self.count % 50000 == 0:
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(PASSIVE)")
            print(f"Imported {self.count} places...")
    
    def node(self, n):
        # Guard against invalid locations
        if not n.location.valid():
            return
        
        tags = n.tags
        name = tags.get("name")
        lat = n.location.lat
        lon = n.location.lon
        
        # Extract address components
        housenumber = tags.get("addr:housenumber", "")
        street = tags.get("addr:street", "")
        city = tags.get("addr:city", "")
        state = tags.get("addr:state", "")
        postcode = tags.get("addr:postcode", "")
        
        # Check if emergency
        is_emerg, emerg_type = is_emergency_type(tags)
        
        # Check if POI or address
        is_poi = any([
            tags.get("amenity"),
            tags.get("shop"),
            tags.get("tourism"),
            tags.get("office"),
            tags.get("craft"),
            tags.get("leisure"),
            tags.get("historic"),
        ])
        
        has_address = housenumber and street
        
        # Skip if neither POI nor address
        if not is_poi and not has_address:
            return
        
        # POI with name (import Northeast-wide)
        if is_poi and name:
            place_type = detect_place_type(tags)

            if not place_type:
                return

            # Build address string
            address_parts = []
            if housenumber and street:
                address_parts.append(f"{housenumber} {street}")
            elif street:
                address_parts.append(street)
            
            if city:
                address_parts.append(city)
            if postcode:
                address_parts.append(postcode)
            
            address = ", ".join(address_parts) if address_parts else None
            
            # Generate geohash
            geohash = geohash_encode(lat, lon)
            
            # Store full JSON only for emergencies
            osm_tags_json = tags_to_json(tags) if is_emerg else None

            try:
                conn.execute(UPSERT_SQL, ("node", n.id, name, lat, lon, place_type, address, city, state, postcode, geohash, False, is_emerg, emerg_type, osm_tags_json))
                
                self.count += 1
                self.maybe_commit()

            except Exception as e:
                print(f"Node import error {n.id}: {e}")
        
        # Address-only node (NH only)
        elif has_address and is_in_nh(lat, lon):
            place_type = "address"
            
            # Build full address
            address_parts = [f"{housenumber} {street}"]
            if city:
                address_parts.append(city)
            if state:
                address_parts.append(state)
            if postcode:
                address_parts.append(postcode)
            
            address = ", ".join(address_parts)
            name = address  # Use full address as the name for searching
            
            # Generate geohash
            geohash = geohash_encode(lat, lon)

            try:
                conn.execute(UPSERT_SQL, ("node", n.id, name, lat, lon, place_type, address, city, state, postcode, geohash, True, False, None, None))
                
                self.count += 1
                self.maybe_commit()

            except Exception as e:
                print(f"Address node import error {n.id}: {e}")

    def way(self, w):
        """Import POIs Northeast-wide and address-only ways in NH"""
        tags = w.tags

        # Address parts
        housenumber = tags.get("addr:housenumber", "")
        street = tags.get("addr:street", "")
        city = tags.get("addr:city", "")
        state = tags.get("addr:state", "")
        postcode = tags.get("addr:postcode", "")

        has_address = bool(housenumber and street)

        # POI detection
        is_poi = any([
            tags.get("amenity"),
            tags.get("shop"),
            tags.get("tourism"),
            tags.get("office"),
            tags.get("craft"),
            tags.get("leisure"),
            tags.get("historic"),
        ])

        # Skip irrelevant ways
        if not is_poi and not has_address:
            return

        # Calculate centroid
        coords = []

        for node in w.nodes:
            if node.location.valid():
                coords.append((node.location.lat, node.location.lon))

        if not coords:
            return

        # Remove duplicated closing polygon node
        if len(coords) > 1 and coords[0] == coords[-1]:
            coords.pop()

        if not coords:
            return

        lat = sum(c[0] for c in coords) / len(coords)
        lon = sum(c[1] for c in coords) / len(coords)

        # NH-only filter for address-only ways
        if has_address and not is_poi:
            if not is_in_nh(lat, lon):
                return

        # Determine name/type
        name = tags.get("name")

        if is_poi:
            if not name:
                return

            place_type = detect_place_type(tags)

            if not place_type:
                return

            is_address_way = False

        else:
            # Address-only way
            name = f"{housenumber} {street}"
            place_type = "address"
            is_address_way = True

        # Build address
        address_parts = []

        if housenumber and street:
            address_parts.append(f"{housenumber} {street}")
        elif street:
            address_parts.append(street)

        if city:
            address_parts.append(city)

        if state:
            address_parts.append(state)

        if postcode:
            address_parts.append(postcode)

        address = ", ".join(address_parts) if address_parts else None

        # Default NH state
        if not state and is_in_nh(lat, lon):
            state = "NH"

        geohash = geohash_encode(lat, lon)

        is_emerg, emerg_type = is_emergency_type(tags)

        osm_tags_json = tags_to_json(tags) if is_emerg else None

        try:
            conn.execute(
                UPSERT_SQL,
                (
                    "way",
                    w.id,
                    name,
                    lat,
                    lon,
                    place_type,
                    address,
                    city,
                    state,
                    postcode,
                    geohash,
                    is_address_way,
                    is_emerg,
                    emerg_type,
                    osm_tags_json,
                ),
            )

            self.count += 1
            self.maybe_commit()

        except Exception as e:
            print(f"Way import error {w.id}: {e}")

print("Starting OSM import...")
print("Importing: All Northeast POIs + addresses + NH home addresses")
print("With geohash, city, state, postcode, emergency data, and full JSON for emergencies")
print()

handler = PlaceHandler()
handler.apply_file(PBF_FILE, locations=True)

conn.commit()
conn.execute("PRAGMA wal_checkpoint(RESTART)")

# Create indexes AFTER import for better performance
print("Creating indexes...")
conn.execute("CREATE INDEX IF NOT EXISTS idx_osm_id ON places(osm_id)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_name_lower ON places(LOWER(name))")
conn.execute("CREATE INDEX IF NOT EXISTS idx_address_lower ON places(LOWER(address))")
conn.execute("CREATE INDEX IF NOT EXISTS idx_geohash ON places(geohash)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_city ON places(city)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_state ON places(state)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON places(type)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_is_emergency ON places(is_emergency)")
conn.execute("CREATE INDEX IF NOT EXISTS idx_lat_lon ON places(lat, lon)")
conn.commit()

conn.close()

print("OSM import complete.")