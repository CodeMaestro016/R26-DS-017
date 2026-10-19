# Authoritative compiled-map coordinate frame

The former operational intersection center was manually configured as the
source-network coordinate `(300, 100)`. SUMO network conversion recorded a
`netOffset` and expresses TraCI positions, compiled lane shapes, movement paths,
conflict zones, and junction nodes in the converted network frame. The manual
source coordinate consequently no longer represented the physical junction.

Operational intersection geometry is now derived from the compiled SUMO
network. Every legal `MapPathManager` movement must connect an incoming edge's
destination to the same outgoing edge's origin. The unique common junction's
`getCoord()` value is the authoritative center in
`SUMO_COMPILED_NETWORK_XY_METERS`.

The compiled `netOffset`, boundaries, and projection parameter are retained as
provenance only. They are not applied to TraCI positions, lane geometry,
movement paths, or conflict zones. In a deployed AV, the equivalent reference
would come from its localized HD map rather than a manually typed Cartesian
coordinate.
