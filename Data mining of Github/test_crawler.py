"""Tests for some of the parts of the crawler."""
import crawler

def test_simple_web_link():
    """Tests if single link in WebLink format can be parsed."""
    weblink = "<http://example.com/Book/chapter2>; rel=\"previous\""
    expected = {'previous': "http://example.com/Book/chapter2"}
    actual = crawler.link_to_dict(weblink)
    assert expected == actual

def test_multiple_web_links():
    """Tests if multiple Weblinks can be parsed."""
    weblink = "<http://example.com/Book/chapter2>; rel=\"previous\", " + \
              "<http://example.com/Book/chapter4>; rel=\"next\", " + \
              "<http://example.com/Book/chapter1>; rel=\"first\""
    expected = {'previous': 'http://example.com/Book/chapter2',
                'next': 'http://example.com/Book/chapter4',
                'first': 'http://example.com/Book/chapter1'}
    actual = crawler.link_to_dict(weblink)
    assert expected == actual

def test_calculate_edge_sizes():
    """Tests if the calculation of thickness for the edgess if right."""
    data = {'a':10, 'b':5}
    expected = [10., 5.]
    actual = crawler.calculate_edge_sizes(data)
    assert expected == actual
