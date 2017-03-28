"""
Download portraits of all members of the current U.S. Congress from
Wikipedia.

This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or
distribute this software, either in source code form or as a compiled
binary, for any purpose, commercial or non-commercial, and by any
means.

In jurisdictions that recognize copyright laws, the author or authors
of this software dedicate any and all copyright interest in the
software to the public domain. We make this dedication for the benefit
of the public at large and to the detriment of our heirs and
successors. We intend this dedication to be an overt act of
relinquishment in perpetuity of all present and future rights to this
software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR
OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <http://unlicense.org/>
"""
import io
import urllib.parse
import shutil
import re
import sys
import traceback
from collections import namedtuple

import lxml.etree
import mwparserfromhell
import requests


CongressProfile = namedtuple('file_name', 'image')

HOUSE_PAGE_NAME = 'Current members of the United States House of ' \
    'Representatives'
HOUSE_SECTION_NAME = 'Voting members by state'
SENATE_PAGE_NAME = 'List of current United States Senators'
SENATE_SECTION_NAME = 'Senators'

RE_SORTNAME = re.compile('\{\{sortname\|(?P<firstname>.*?)\|(?P<lastname>.*?)(?P<articlename>\|.*?)?\}\}')

def main():

    senators = current_members(SENATE_PAGE_NAME, SENATE_SECTION_NAME)
    representatives = current_members(HOUSE_PAGE_NAME, HOUSE_SECTION_NAME)
    print('loading images for {} senators and {} representatives'.format(len(senators), len(representatives)))

    failures = []
    for fname, lname, article_name in senators + representatives:
        article_name = article_name.lstrip('|') if article_name \
                       else fname + ' ' + lname
        img_file_name = 'us_congress_portrait_{}_{}.jpg'.format(lname.lower(),
                                                                fname.lower())
        sys.stdout.write('{}, {}...'.format(lname, fname))
        try:
            with open(img_file_name, 'wb') as img_file:
                download_congress_portrait(str(article_name), img_file)
        except:
            sys.stdout.write(' FAILED.\n')
            traceback.print_exc()
            failures.append('{}, {}'.format(lname, fname))
        else:
            sys.stdout.write(' OK\n')

    print('failures:\n{}'.format('\n'.join(sorted(failures))))


def current_members(page_name, section_name):
    page_text = wiki_query_article(page_name)
    page = mwparserfromhell.parse(page_text)
    page_sections = page.get_sections(matches=section_name)
    assert len(page_sections) == 1
    section = page_sections[0]
    return RE_SORTNAME.findall(str(section))

    
def download_congress_portrait(page_title, img_file):
    """Store an office holder's Wikipedia portrait in a file
    
    :param page_title: office holder's Wikipedia page title
    :param img_file: file to store the image
    """
    page_text = wiki_query_article(page_title)
    image_name = wiki_read_officeholder_image_name(page_text)
    image_url = wiki_query_image_url(image_name)

    image_response = requests.get(image_url, stream=True)
    image_response.raise_for_status()
    image_response.raw.decode_content = True
    shutil.copyfileobj(image_response.raw, img_file)


def wiki_read_officeholder_image_name(page_text):
    """Get an office holder's portrait name from a Wikipedia article

    Assumes there is exactly one officeholder infobox for the subject,
    and that the image in the info box is the office holder's portrait.

    :param page_text: article text, in WikiMarkdown
    :return: unicode file name of portrait
    """
    templates = mwparserfromhell.parse(page_text).filter_templates()
    infoboxen = [template for template in templates
                 if template.name.strip().lower() in
        ('infobox officeholder', 'infobox senator', 'infobox congressman', \
         'infobox politician', 'infobox politician (general)')]
    assert len(infoboxen) == 1, 'templates = {}'.format(templates)
    infobox = infoboxen[0]

    return infobox.get('image').value.strip()

def wiki_query_article(title):
    """Retrieve the text of a Wikipedia article with the given title

    :param title: title of the article to retrieve
    :return: text of the latest revision of the article
        (in WikiMarkdown)
    """
    params = {
        'format': 'xml',
        'action': 'query',
        'prop': 'revisions',
        'rvprop': 'timestamp|user|comment|content',
        'titles': 'API|{}'.format(urllib.parse.quote(title.encode('utf8')))
    }

    tree = wiki_query(**params)
    revs = tree.xpath('//rev')
    return revs[-1].text


def wiki_query_image_url(file_name):
    """Retrieve the URL for a given image file on Wikipedia
    :param file_name: file to get -- OMIT the 'File:' prefix
    :return: unicode image URL
    """
    query_title = 'File:{}'.format(file_name)
    params = {
        'format': 'xml',
        'action': 'query',
        'prop': 'imageinfo',
        'iiprop': 'url',
        'titles': 'API|{}'.format(query_title)
    }
    tree = wiki_query(**params)

    response_title = query_title
    all_normalized = tree.xpath('//normalized/n')
    for normalized in all_normalized:
        if normalized.get('from') == query_title:
            response_title = normalized.get('to')

    pages = tree.xpath('//page[@title="{}"]'.format(response_title))
    assert len(pages) == 1, 'tree = {}'.format(lxml.etree.tostring(tree))
    page = pages[0]
    ii = page.xpath('//ii')
    assert len(ii) == 1, 'pages = {}'.format([lxml.etree.tostring(page)
                                              for page in pages])

    return ii[0].get('url')


def wiki_query(**kwargs):
    """Query the Wikipedia API

    :param kwargs: parameters to pass to the API
    :return: lxml element tree with the response
    """
    qs = '&'.join('%s=%s' % (k, v)  for k, v in kwargs.items())
    url = 'http://en.wikipedia.org/w/api.php?{}'.format(qs)
    response = requests.get(url)

    return lxml.etree.parse(io.StringIO(response.text))


if __name__ == '__main__':
    main()
