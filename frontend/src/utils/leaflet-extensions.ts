import L from 'leaflet';

// Fix for marker animation during zoom
L.Marker.prototype._animateZoom = function (opt: { zoom: number; center: L.LatLng }) {
    if (!this._map) {
        return;
    }

    const pos = this._map._latLngToNewLayerPoint(this._latlng, opt.zoom, opt.center).round();

    this._setPos(pos);
};

// Fix for popup animation during zoom
L.Popup.prototype._animateZoom = function (opt: { zoom: number; center: L.LatLng }) {
    if (!this._map) {
        return;
    }
    
    const anchor = L.point(this._containerLeft, this._containerBottom);
    const pos = this._map._latLngToNewLayerPoint(this._latlng, opt.zoom, opt.center);
    
    const offset = L.point(this.options.offset);
    anchor._add(offset);
    
    const newPos = pos.subtract(anchor);
    this._container.style.left = newPos.x + 'px';
    this._container.style.top = newPos.y + 'px';
}; 