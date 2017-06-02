#!/usr/bin/env python3

import json
import fileinput
import re
from collections import defaultdict, Counter, OrderedDict


if __name__ == '__main__':
    pat = re.compile(r'\S+ '
                     '(?P<ip>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - '  # IP address
                     '\[.+\] '  # datetime
                     '"\w{3,6} (?P<req>\S+) \w{0,4}/\d\.\d" '  # requested file
                     '(?P<status>[23]\d\d) '  # status
                     '\d+ '  # bandwidth
                     '"(?P<referrer>.+)" '  # referrer
                     '"(?P<useragent>.+)"'  # user agent
                     )

    skipreq = re.compile(
        r'/(?:(?:favicon.ico$)|(?:ws|search|static)[/?])'
    )

    userreq = re.compile(
        r'/user/'
    )

    entityreq = re.compile(
        r'(/(?:release|artist|event|release-group)/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})/?'
    )

    sitemapreq = re.compile(
        r'/sitemap-'
    )

    def constant_factory(value):
        return lambda: value

    top = defaultdict(constant_factory(20))
    top['req'] = 50
    top['sitemap'] = 10
    count_keys = ['ip', 'status', 'req', 'referrer', 'useragent', 'userreq',
                  'sitemap']
    counts = {}
    for key in count_keys:
        counts[key] = defaultdict(int)

    with fileinput.input() as f:
        for line in f:
            res = re.search(pat, line)
            if res:
                elements = res.groupdict()
                if re.search(skipreq, elements['req']):
                    continue
                if re.search(userreq, elements['req']):
                    elements['userreq'] = elements['req']
                else:
                    m = re.search(entityreq, elements['req'])
                    if m:
                        elements['req'] = m.group(1)
                    else:
                        m = re.search(sitemapreq, elements['req'])
                        if m:
                            elements['req'] = 'sitemaps'
                            elements['sitemap'] = elements[
                                'ip'] + ' ' + elements['useragent']
                for key in count_keys:
                    if key in elements:
                        counts[key][elements[key]] += 1

    output = OrderedDict()
    counters = {}
    for key in count_keys:
        counters[key] = Counter(counts[key])
        topkey = "Top %s" % key
        output[topkey] = dict()
        output[topkey]['topn'] = top[key]
        output[topkey]['total'] = total = sum(counters[key].values())
        output[topkey]['records'] = list()
        for k, v in counters[key].most_common(top[key]):
            output[topkey]['records'].append({
                'key': k,
                'value': int(v),
                'percent': round(100 * v / float(total), 2)
            })
    print(json.dumps(output, indent=4, separators=(',', ': ')))
