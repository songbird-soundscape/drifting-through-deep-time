"""Minimal reader for GPlates GPML polygon features (plate ID, name, valid time, rings)."""
import xml.etree.ElementTree as ET
NS = {'gpml': 'http://www.gplates.org/gplates', 'gml': 'http://www.opengis.net/gml'}
G = '{http://www.gplates.org/gplates}'

def _t(v):
    v = (v or '').strip().lower()
    if v in ('http://gplates.org/times/distantpast', 'distantpast'): return float('inf')
    if v in ('http://gplates.org/times/distantfuture', 'distantfuture'): return float('-inf')
    return float(v)

def read(path):
    out = []
    root = ET.parse(path).getroot()
    for fm in root.findall('gml:featureMember', NS):
        f = list(fm)[0]
        pid = f.find('gpml:reconstructionPlateId/gpml:ConstantValue/gpml:value', NS)
        pid = int(pid.text) if pid is not None else 0
        attrs = {}
        for el in f.iter(G + 'KeyValueDictionaryElement'):
            k = el.find('gpml:key', NS).text; v = el.find('gpml:value', NS)
            attrs[k] = v.text if v is not None else None
        tp = f.findall('gpml:validTime/gml:TimePeriod/*/gml:TimeInstant/gml:timePosition', NS)
        if len(tp) == 2: begin, end = _t(tp[0].text), _t(tp[1].text)
        else: begin, end = float(attrs.get('FROMAGE') or 4000), float(attrs.get('TOAGE') or 0)
        rings = []
        for pl in f.iter('{http://www.opengis.net/gml}posList'):
            v = [float(x) for x in pl.text.split()]
            rings.append([(v[i + 1], v[i]) for i in range(0, len(v), 2)])  # GPML is lat lon -> (lon, lat)
        if rings: out.append(dict(pid=pid, name=attrs.get('NAME') or '', begin=begin, end=end, rings=rings))
    return out
