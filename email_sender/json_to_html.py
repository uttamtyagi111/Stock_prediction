import json
from bs4 import BeautifulSoup

def html_to_json(html):
    """
    Convert HTML to JSON according to the specified structure
    """
    soup = BeautifulSoup(html, 'html.parser')
    json_data = []

    # Process the whole HTML structure, not just rows and cells
    for element in soup.find_all(['img', 'p', 'h1', 'table']):
        if element.name == 'img':
            element_json = {
                "id": "",
                "type": "image",
                "values": {
                    "containerPadding": "",
                    "anchor": "",
                    "src": {
                        "url": element.get('src'),
                        "width": int(element.get('width', 0)),
                        "height": int(element.get('height', 0))
                    },
                    "textAlign": "",
                    "altText": element.get('alt'),
                    "action": {
                        "name": "",
                        "values": {
                            "href": "",
                            "target": ""
                        }
                    },
                    "hideDesktop": False,
                    "displayCondition": None,
                    "_meta": {
                        "htmlID": element.get('id'),
                        "htmlClassNames": ' '.join(element.get('class', []))
                    },
                    "selectable": True,
                    "draggable": True,
                    "duplicatable": True,
                    "deletable": True,
                    "hideable": True
                }
            }
            json_data.append(element_json)
        
        elif element.name == 'p':
            element_json = {
                "id": "",
                "type": "paragraph",
                "values": {
                    "text": element.get_text(),
                    "fontSize": "15px",
                    "lineHeight": "24px",
                    "fontFamily": "Helvetica, Arial, sans-serif",
                    "fontWeight": "400",
                    "textDecoration": "none",
                    "color": "#000000",
                    "_meta": {
                        "htmlID": element.get('id'),
                        "htmlClassNames": ' '.join(element.get('class', []))
                    }
                }
            }
            json_data.append(element_json)
        
        elif element.name == 'h1':
            element_json = {
                "id": "",
                "type": "heading",
                "values": {
                    "text": element.get_text(),
                    "fontSize": "22px",
                    "lineHeight": "24px",
                    "fontFamily": "Helvetica, Arial, sans-serif",
                    "fontWeight": "normal",
                    "textDecoration": "none",
                    "color": "#000000",
                    "_meta": {
                        "htmlID": element.get('id'),
                        "htmlClassNames": ' '.join(element.get('class', []))
                    }
                }
            }
            json_data.append(element_json)
        
        elif element.name == 'table':
            # Process table structure (including rows and cells)
            table_json = {
                "type": "table",
                "values": {
                    "rows": []
                }
            }
            for row in element.find_all('tr'):
                row_json = {
                    "id": "",
                    "cells": [],
                    "values": {}
                }
                for cell in row.find_all('td'):
                    cell_json = {
                        "id": "",
                        "contents": [],
                        "values": {
                            "_meta": {
                                "htmlID": cell.get('id'),
                                "htmlClassNames": ' '.join(cell.get('class', []))
                            },
                            "border": {},
                            "padding": "",
                            "borderRadius": "",
                            "backgroundColor": ""
                        }
                    }
                    for content in cell.contents:
                        if content.name == 'img':
                            content_json = {
                                "id": "",
                                "type": "image",
                                "values": {
                                    "containerPadding": "",
                                    "anchor": "",
                                    "src": {
                                        "url": content.get('src'),
                                        "width": int(content.get('width', 0)),
                                        "height": int(content.get('height', 0))
                                    },
                                    "textAlign": "",
                                    "altText": content.get('alt'),
                                    "action": {
                                        "name": "",
                                        "values": {
                                            "href": "",
                                            "target": ""
                                        }
                                    },
                                    "hideDesktop": False,
                                    "displayCondition": None,
                                    "_meta": {
                                        "htmlID": content.get('id'),
                                        "htmlClassNames": ' '.join(content.get('class', []))
                                    },
                                    "selectable": True,
                                    "draggable": True,
                                    "duplicatable": True,
                                    "deletable": True,
                                    "hideable": True
                                }
                            }
                            cell_json["contents"].append(content_json)
                    row_json["cells"].append(cell_json)
                table_json["values"]["rows"].append(row_json)
            json_data.append(table_json)

    return json.dumps({"elements": json_data}, indent=2)


html_content = """<!DOCTYPE HTML PUBLIC "-//W3C//DTD XHTML 1.0 Transitional //EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:v="urn:schemas-microsoft-com:vml" xmlns:o="urn:schemas-microsoft-com:office:office">
<head>
  <!--[if gte mso 9]>
  <xml>
    <o:OfficeDocumentSettings>
      <o:AllowPNG/>
      <o:PixelsPerInch>96</o:PixelsPerInch>
    </o:OfficeDocumentSettings>
  </xml>
  <![endif]-->
  <meta http-equiv="Content-Type" content="text/html; charset=UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="x-apple-disable-message-reformatting">
  <!--[if !mso]><!--><meta http-equiv="X-UA-Compatible" content="IE=edge"><!--<![endif]-->
    <!-- Your title goes here -->
    <title>You're Invited</title>
    <!-- End title -->
    <!-- Start stylesheet -->
    <style type="text/css">
      a,a[href],a:hover, a:link, a:visited {
        /* This is the link colour */
        text-decoration: none!important;
        color: #0000EE;
      }
      .link {
        text-decoration: underline!important;
      }
      p, p:visited {
        /* Fallback paragraph style */
        font-size:15px;
        line-height:24px;
        font-family:'Helvetica', Arial, sans-serif;
        font-weight:300;
        text-decoration:none;
        color: #000000;
      }
      h1 {
        /* Fallback heading style */
        font-size:22px;
        line-height:24px;
        font-family:'Helvetica', Arial, sans-serif;
        font-weight:normal;
        text-decoration:none;
        color: #000000;
      }
      .ExternalClass p, .ExternalClass span, .ExternalClass font, .ExternalClass td {line-height: 100%;}
      .ExternalClass {width: 100%;}
    </style>
    <!-- End stylesheet -->
</head>
  <!-- You can change background colour here -->
  <body style="text-align: center; margin: 0; padding-top: 10px; padding-bottom: 10px; padding-left: 0; padding-right: 0; -webkit-text-size-adjust: 100%;background-color: #F2F4F6; color: #000000" align="center">
  <!-- Fallback force center content -->
  <div style="text-align: center;">
    <!-- Start container for logo -->
    <table align="center" style="text-align: center; vertical-align: top; width: 600px; max-width: 600px; background-color: #000000;" width="600">
      <tbody>
        <tr>
          <td style="width: 596px; vertical-align: top; padding-left: 0; padding-right: 0; padding-top: 15px; padding-bottom: 15px;" width="596">
            <!-- Your logo is here -->
            <img style="width: 540px; max-width: 540px; height: 255px; max-height: 255px; text-align: center; color: #FFFFFF;" alt="Logo" src="https://i.postimg.cc/MTxdDrrY/Logos.png" align="center" width="180" height="85">
          </td>
        </tr>
      </tbody>
    </table>
    <!-- End container for logo -->
    <!-- Hero image -->
    <img style="width: 600px; max-width: 600px; height: 497px; max-height: 497px; text-align: center;" alt="Hero image" src="https://i.postimg.cc/fyPPBfdT/Gsm.png" align="center" width="600" height="350">
    <!-- Hero image -->
    <!-- Start single column section -->
    <table align="center" style="text-align: center; vertical-align: top; width: 600px; max-width: 600px; background-color: #000000;" width="600">
        <tbody>
          <tr>
            <td style="width: 596px; vertical-align: top; padding-left: 0; padding-right: 0; padding-top: 30px; padding-bottom: 30px; text-align: center; color: #ffffff;" width="596">
              <!-- Title -->
              <h1>You're Invited!</h1>
              <!-- Title -->
              <!-- Text -->
              <p>This is a friendly reminder about our upcoming event. We hope to see you there!</p>
              <!-- Text -->
            </td>
          </tr>
        </tbody>
    </table>
    <!-- End single column section -->
    <!-- Start footer -->
    <table align="center" style="text-align: center; vertical-align: top; width: 600px; max-width: 600px; background-color: #000000;" width="600">
        <tbody>
          <tr>
            <td style="width: 596px; vertical-align: top; padding-left: 0; padding-right: 0; padding-top: 30px; padding-bottom: 30px; text-align: center; color: #ffffff;" width="596">
              <!-- Footer content -->
              <p>&copy; 2024 Company Name. All rights reserved.</p>
            </td>
          </tr>
        </tbody>
    </table>
    <!-- End footer -->
  </div>
</body>
</html>"""

json_output = html_to_json(html_content)
print(json_output)
