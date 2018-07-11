from __future__ import print_function
from requests.exceptions import HTTPError

"""
Retrieved from https://github.com/lukasschwab/arxiv.py/blob/master/arxiv/arxiv.py

LICENSE

Copyright (c) 2015 Lukas Schwab

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

try:
    # Python 2
    from urllib import quote_plus
    from urllib import urlencode
    from urllib import urlretrieve
except ImportError:
    # Python 3
    from urllib.parse import quote_plus
    from urllib.parse import urlencode
    from urllib.request import urlretrieve
import feedparser

root_url = 'http://export.arxiv.org/api/'


def query(
    search_query="",
    id_list=[],
    prune=True,
    start=0,
    max_results=10,
    sort_by="relevance",
    sort_order="descending"
):
    url_args = urlencode({"search_query": search_query,
                          "id_list": ','.join(id_list),
                          "start": start,
                          "max_results": max_results,
                          "sortBy": sort_by,
                          "sortOrder": sort_order})
    results = feedparser.parse(root_url + 'query?' + url_args)
    if results.get('status') != 200:
        # TODO: better error reporting
        raise Exception("HTTP Error " + str(results.get('status', 'no status')) + " in query")
    else:
        entries = results['entries']
        meta = results['feed']
    for entry in entries:
        # Renamings and modifications
        mod_query_result(entry)
        if prune:
            prune_query_result(entry)
    return entries, meta


def mod_query_result(result):
    # Useful to have for download automation
    result['pdf_url'] = None
    for link in result['links']:
        if 'title' in link and link['title'] == 'pdf':
            result['pdf_url'] = link['href']
    result['affiliation'] = result.pop('arxiv_affiliation', 'None')
    result['arxiv_url'] = result.pop('link')
    result['title'] = result['title'].rstrip('\n')
    result['summary'] = result['summary'].rstrip('\n')
    result['authors'] = [d['name'] for d in result['authors']]
    if 'arxiv_comment' in result:
        result['arxiv_comment'] = result['arxiv_comment'].rstrip('\n')
    else:
        result['arxiv_comment'] = None
    if 'arxiv_journal_ref' in result:
        result['journal_reference'] = result.pop('arxiv_journal_ref')
    else:
        result['journal_reference'] = None
    if 'arxiv_doi' in result:
        result['doi'] = result.pop('arxiv_doi')
    else:
        result['doi'] = None


def prune_query_result(result):
    prune_keys = ['updated_parsed',
                  'published_parsed',
                  'arxiv_primary_category',
                  'summary_detail',
                  'author',
                  'author_detail',
                  'links',
                  'guidislink',
                  'title_detail',
                  'tags',
                  'id']
    for key in prune_keys:
        try:
            del result['key']
        except KeyError:
            pass


def to_slug(title):
    # Remove special characters
    filename = ''.join(c if c.isalnum() else '_' for c in title)
    # delete duplicate underscores
    filename = '_'.join(list(filter(None, filename.split('_'))))
    return filename


def download(obj, dirname='./', prepend_id=False, slugify=False):
    # Downloads file in obj (can be result or unique page) if it has a .pdf link
    if 'pdf_url' in obj and 'title' in obj and obj['pdf_url'] and obj['title']:
        filename = obj['title']
        if slugify:
            filename = to_slug(filename)
        if prepend_id:
            filename = obj['arxiv_url'].split('/')[-1] + '-' + filename
        filename = dirname + filename + '.pdf'
        # Download
        urlretrieve(obj['pdf_url'], filename)
        return filename
    else:
        print("Object obj has no PDF URL, or has no title")
