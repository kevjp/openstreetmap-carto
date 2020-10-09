@amenity-brown: #734a08;
@gastronomy-icon: #C77400;


#agents {
    [zoom >= 17] {
    marker-fill: @gastronomy-icon;
    marker-width: 4;
    [zoom >= 19] {
            marker-file: url('symbols/amenity/cafe.svg');
            marker-width: 12;
        }
    }
}
