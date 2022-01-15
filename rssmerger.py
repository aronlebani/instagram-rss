import sys
import socket
import urllib.request
import urllib.error
import time
import getopt
import xml.dom.minidom

rssItemsMax = 60
silent = 0
verbose = 0
queries = False

def rssFetch(url):
    """
    Fetch a RSS file from somewhere.
    """

    try:
        f_rss = urllib.request.urlopen(url)
    except:
        if not silent and url != 'merged.rss' and url != 'seen.rss':
            print("Failed to retrieve RSS feed %s" % (url))
            raise
        return False

    return f_rss.read()

def rssWrite (filename, channelTitle, channelDescription, channelLink, items):
    """
    Write items to a RSS2.0 file
    """

    rssNew = xml.dom.minidom.Document()
    elemRss = rssNew.createElementNS("http://blogs.law.harvard.edu/tech/rss", "rss")
    elemRss.setAttribute("version", "2.0")

    elemChannel = rssNew.createElement("channel")
    elemChannel.appendChild(createElementText("title", channelTitle))
    elemChannel.appendChild(createElementText("link", channelLink))
    elemChannel.appendChild(createElementText("description", channelDescription))

    for item in items:
        elemChannel.appendChild(rssComposeItem(item))

    elemRss.appendChild(elemChannel)
    rssNew.appendChild(elemRss)

    rssFile = open(filename, "w")
    rssFile.write(rssNew.toprettyxml())
    rssFile.close()


def createElementText (element, text):
    """
    Create an XML DOM element with a child Text node and return it
    """

    elemNew = xml.dom.minidom.Document().createElement(element)
    textNew = xml.dom.minidom.Document().createTextNode(text)
    elemNew.appendChild(textNew)

    return elemNew

def createElementTextNS (namespace, element, text):
    """
    Create an XML DOM element with a child Text node and return it
    """

    elemNew = xml.dom.minidom.Document().createElementNS(namespace, element)
    elemNew.setAttribute("xmlns:" + element.split(':', 1)[0], namespace)
    textNew = xml.dom.minidom.Document().createTextNode(text)
    elemNew.appendChild(textNew)

    return elemNew


def rssComposeItem (item):
    """
    Composes a RSS <item> element from the item dict
    """

    elemItem = xml.dom.minidom.Document().createElement("item")

    elemItem.appendChild(createElementText("title", item["title"]))
    elemItem.appendChild(createElementText("link", item["link"]))
    elemItem.appendChild(createElementText("date", item["date"]))
    elemItem.appendChild(createElementTextNS("http://localhost/rssmerger/", "rm:publisher", item["publisher"]))
    if "description" not in item:
        elemItem.appendChild(createElementText("description", item["description"]))

    return elemItem


def rssItemElementGetData (node, rssID):
    global verbose
    if hasattr(node, 'data'):
        return(node.data.strip())
    else:
        if verbose:
            print("Node has no data in %s! (HTML tag in data?)" % (rssID))
        return("??")

def rssExtractItem (node, rssID):
    """
    Given an <item> node, extract all possible RSS information from the node
    """

    rssItem = {
        "title": "No title",
        "link": "http://localhost/",
        "description": "No description",
        "publisher": rssID,
        "date": time.strftime("%a, %d %b %Y %H:%M:%S +0000", time.gmtime())
    }

    for childNode in node.childNodes:
        if childNode.firstChild != None:
            if childNode.nodeName == "title":
                rssItem["title"] = rssItemElementGetData(childNode.firstChild, rssID)
            if childNode.nodeName == "link":
                rssItem["link"] = rssItemElementGetData(childNode.firstChild, rssID)
            if childNode.nodeName == "description":
                rssItem["description"] = rssItemElementGetData(childNode.firstChild, rssID)
            if childNode.nodeName == "content:encoded":
                rssItem["description"] = rssItemElementGetData(childNode.firstChild, rssID)
            if childNode.nodeName == "rm:publisher":
                rssItem["publisher"] = rssItemElementGetData(childNode.firstChild, rssID)
            if childNode.nodeName == "date":
                rssItem["date"] = rssItemElementGetData(childNode.firstChild, rssID)

    if verbose:
        print("\t\tItem: " + rssItem["publisher"].encode('ascii', 'replace') + ": " + rssItem["title"].encode('ascii', 'replace'))

    return rssItem

def rssFindItems(node, rssItems, rssID):
    """
    Walk through a XML DOM and take action upon finding <item> nodes
    """

    if node.nodeType == xml.dom.Node.ELEMENT_NODE:
        for childNode in node.childNodes:
            if childNode.nodeName == "item":
                rssItems.append(rssExtractItem(childNode, rssID))
            else:
                rssFindItems(childNode, rssItems, rssID)

    return (rssItems)

def combine(rssUrls):
    # Set default socket timeout so urllib doesn't hang when retrieving RSS feeds
    socket.setdefaulttimeout(10)

    # Get seen items
    rssItemsSeen = []
    try:
        rssSeen = rssFetch("merged.rss")
        if rssSeen:
            root = xml.dom.minidom.parseString(rssSeen)
        else:
            root = xml.dom.minidom.Document()
    except:
        if not silent:
            print("Cannot parse merged.rss: " + str(sys.exc_info()[1]))
            raise
    else:
        # Extract all seen items
        if rssSeen:
            node = root.firstChild
            rssItemsSeen = rssFindItems(node, rssItemsSeen, "seen")

    # Get last seen items (to determine which items are new)
    rssItemsLastSeen = []
    try:
        rssSeen = rssFetch("seen.rss")
        if rssSeen:
            root = xml.dom.minidom.parseString(rssSeen)
        else:
            root = xml.dom.minidom.Document()
    except:
        if not silent:
            print("Cannot parse seen.rss: " + str(sys.exc_info()[1]))
            raise
    else:
        # Extract all seen items
        if rssSeen:
            node = root.firstChild
            rssItemsLastSeen = rssFindItems(node, rssItemsLastSeen, "lastseen")

    # Merge seen items and new published items
    rssItemsMerged = []
    rssItemsNew = []
    rssItemsNewLastSeen = []

    for rssID in rssUrls.keys():
        if verbose:
            print("Processing %s" % (rssID))

        rssItemsPub = []

        # Read published items
        try:
            if verbose:
                print("\tRetrieving %s" % (rssUrls[rssID]))
            rssPub = rssFetch(rssUrls[rssID])
            if not rssPub:
                if not silent:
                    print("\tError")
            else:
                if verbose:
                    print("\tRetrieved.")
            root = xml.dom.minidom.parseString(rssPub)
        except:
            if not silent:
                print("Cannot parse " + rssUrls[rssID] + ": " + str(sys.exc_info()[1]))
        else:
            # Walk through all root-items (handles xml-stylesheet, etc)
            for rootNode in root.childNodes:
                if rootNode.nodeType == xml.dom.Node.ELEMENT_NODE:
                    # Extract all items
                    node = rootNode
                    if verbose:
                        print("\tFinding all published items in '%s'" % (rssID))

                    rssItemsPub = rssFindItems(node, rssItemsPub, rssID)

                    if len(rssItemsPub) > 0:
                        # Find last seen item for this feed
                        lastId = -1
                        for i in range(len(rssItemsLastSeen)):
                            if verbose:
                                print("Find last seen: " + rssItemsLastSeen[i]["publisher"].encode('ascii', 'replace') + " - " + rssID)
                            if rssItemsLastSeen[i]["publisher"] == rssID:
                                lastId = i

                        rssItemLastSeenTitle = ""
                        if lastId > -1:
                            rssItemLastSeenTitle = rssItemsLastSeen[lastId]["title"]
                            if verbose:
                                print("\tLast seen for " + rssID + ": " + rssItemLastSeenTitle.encode('ascii', 'replace'))

                        # First extract all new rss items
                        for rssItem in rssItemsPub:
                            if rssItem["title"] == rssItemLastSeenTitle:
                                # No more new items, stop extracting from published
                                break
                            else:
                                # Ah, a new item. Let's add it to the merged list of seen and unseen items
                                if len(rssItemsMerged) < rssItemsMax:
                                    rssItemsMerged.append (rssItem)
                                # Also add it to a seperate list of all new items
                                rssItemsNew.append(rssItem)

                        # Save the new latest seen item
                        rssItemsNewLastSeen.append (rssItemsPub[0])

    # Now add all items we've already seen to the list too.
    for rssItem in rssItemsSeen:
        if len(rssItemsMerged) < rssItemsMax:
            rssItemsMerged.append (rssItem)

    # find feeds which don't have a 'last seen' item anymore due to errors in
    # the rss feed or something and set it back to the previous last seen item
    for rssID in rssUrls.keys():
        found = 0;
        for rssItem in rssItemsNewLastSeen:
            if rssItem["publisher"] == rssID:
                found = 1;

        if found == 0:
            # Find old last seen item
            for rssItem in rssItemsLastSeen:
                if rssItem["publisher"] == rssID:
                    rssItemsNewLastSeen.append (rssItem)

    if queries:
        rssItemsNew.reverse()
        for rssItem in rssItemsNew:
            # Remove Unicode encodings for Database.
            for property in rssItem:
                rssItem[property] = rssItem[property].encode('ascii', 'replace')
            qry = "INSERT INTO rssitems (title, link, date, publisher, description) VALUES ('%s','%s','%s','%s', '%s');" % (rssItem["title"].replace('\'', '\\\''), rssItem["link"].replace('\'', '\\\''), rssItem["date"].replace('\'', '\\\''), rssItem["publisher"].replace('\'', '\\\''), rssItem["description"].replace('\'', '\\\''))
            print(qry)
    else:
        # Write the new merged list of items to a rss file
        try:
            rssWrite (
                "merged.rss",
                "rssmerger Merged items",
                "This file contains items which have been merged from various RSS feeds",
                "http://www.electricmonk.nl",
                rssItemsMerged
            )
        except IOError:
            if not silent:
                print("couldn't write merged.rss file" + str(sys.exc_value))
        except:
            if not silent:
                print("Unknow error: " + str(sys.exc_value))

    # Write the new list of seen items to a rss file
    try:
        rssWrite (
        "seen.rss",
        "rssmerger Seen items",
        "This file contains the last seen items for each feed",
        "http://www.electricmonk.nl",
        rssItemsNewLastSeen
        )
    except IOError:
        if not silent:
            print("couldn't write merged.rss file" + str(sys.exc_value))
    except:
        if not silent:
            print("Unknow error: " + str(sys.exc_value))
