import zipfile, xml.etree.ElementTree as ET
from pathlib import Path
NS={'a':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
path=Path('Income.xlsx')
with zipfile.ZipFile(path) as zf:
    shared=[]
    if 'xl/sharedStrings.xml' in zf.namelist():
        root=ET.fromstring(zf.read('xl/sharedStrings.xml'))
        for si in root.findall('a:si',NS):
            shared.append(''.join(node.text or '' for node in si.iterfind('.//a:t',NS)))
    rel_root=ET.fromstring(zf.read('xl/_rels/workbook.xml.rels'))
    rel_map={rel.attrib['Id']:rel.attrib['Target'] for rel in rel_root}
    workbook=ET.fromstring(zf.read('xl/workbook.xml'))
    def read_sheet(name):
        for sheet in workbook.find('a:sheets',NS):
            if sheet.attrib['name']==name:
                target=rel_map[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
                root=ET.fromstring(zf.read('xl/'+target))
                rows=root.find('a:sheetData',NS)
                result=[]
                if rows is None:
                    return result
                for row in rows.findall('a:row',NS):
                    cells=[]
                    for cell in row.findall('a:c',NS):
                        t=cell.attrib.get('t')
                        val_node=cell.find('a:v',NS)
                        if t=='inlineStr':
                            val=''.join(node.text or '' for node in cell.iterfind('.//a:t',NS))
                        elif t=='s' and val_node is not None:
                            val=shared[int(val_node.text)] if val_node.text else ''
                        elif val_node is not None:
                            val=val_node.text
                        else:
                            val=''
                        cells.append(val)
                    result.append(cells)
                return result
        return []
    earnings=read_sheet('Earnings')
    for idx,row in enumerate(earnings[:10]):
        print(idx,row)
    print('total',len(earnings))
