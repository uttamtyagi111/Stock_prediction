from bs4 import BeautifulSoup
import json

def parse_html_to_json(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    
    def parse_element(element):
        if element.name == 'img':
            return {
                "type": "image",
                "values": {
                    "src": element.get('src', ''),
                    "alt": element.get('alt', ''),
                    "width": element.get('width', 'auto'),
                    "height": element.get('height', 'auto'),
                    "align": element.get('align', 'center')
                }
            }
        elif element.name in ['h1', 'h2', 'h3', 'h4']:
            return {
                "type": "text",
                "values": {
                    "text": str(element),
                    "align": "left",
                    "padding": "0px 0px"
                }
            }
        elif element.name == 'p':
            return {
                "type": "text",
                "values": {
                    "text": str(element),
                    "align": "left",
                    "padding": "0px 0px"
                }
            }
        elif element.name == 'a':
            style = element.get('style', '')
            return {
                "type": "button",
                "values": {
                    "text": str(element),
                    "url": element.get('href', '#'),
                    "backgroundColor": extract_style_property(style, 'background-color'),
                    "color": extract_style_property(style, 'color'),
                    "padding": extract_style_property(style, 'padding'),
                    "borderRadius": extract_style_property(style, 'border-radius'),
                    "align": "center"
                }
            }
        return None
    
    def extract_style_property(style, property_name):
        for part in style.split(';'):
            if property_name in part:
                return part.split(':')[1].strip()
        return ''
    
    json_output = {"body": {"rows": []}}
    for element in soup.find_all(recursive=True):
        parsed_element = parse_element(element)
        if parsed_element:
            json_output["body"]["rows"].append(parsed_element)
    
    return json_output

# File path
file_path = r'C:\Users\Wish\Downloads\New folder\New folder\Django-API\email_templates\code2.html'

# Read HTML file and convert to JSON
with open(file_path, 'r', encoding='utf-8') as file:
    html_content = file.read()

json_result = parse_html_to_json(html_content)

# Save JSON result to file
output_path = 'output.json'
with open(output_path, 'w', encoding='utf-8') as json_file:
    json.dump(json_result, json_file, indent=4)

print(f"Conversion completed. Check {output_path} for the result.")
