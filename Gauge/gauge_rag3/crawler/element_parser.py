"""
crawler/element_parser.py  —  imported by web_crawler.py, do not run directly.
"""
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

logger = logging.getLogger(__name__)

def _safe(el, attr):
    try:
        v = el.get_attribute(attr); return v.strip() if v else ""
    except: return ""

def _selector(el):
    if v := _safe(el, "id"):            return {"type": "id",   "value": v}
    if v := _safe(el, "name"):          return {"type": "name", "value": v}
    if v := _safe(el, "data-testid"):   return {"type": "css",  "value": f"[data-testid='{v}']"}
    if v := _safe(el, "aria-label"):    return {"type": "css",  "value": f"[aria-label='{v}']"}
    try:
        tag = el.tag_name; cls = _safe(el, "class")
        return {"type": "css", "value": f"{tag}.{cls.split()[0]}"} if cls else {"type": "xpath", "value": f"//{tag}"}
    except: return {"type": "xpath", "value": "//unknown"}

def _desc(el):
    try:
        tag = el.tag_name; text = el.text.strip()[:50] if el.text else ""
        ph = _safe(el,"placeholder"); aria = _safe(el,"aria-label"); tp = _safe(el,"type")
        p = [f"<{tag}"]
        if tp: p.append(f" type='{tp}'")
        if text: p.append(f"> '{text}'")
        elif ph: p.append(f" placeholder='{ph}'>")
        elif aria: p.append(f" aria-label='{aria}'>")
        else: p.append(">")
        return "".join(p)
    except: return "unknown"

class ElementParser:
    def extract_interactive(self, driver: WebDriver) -> list:
        items = []
        for btn in driver.find_elements(By.TAG_NAME, "button"):
            try:
                if not btn.is_displayed(): continue
                items.append({"element_type":"button","text":btn.text.strip()[:80],"selector":_selector(btn),"description":_desc(btn),"disabled":_safe(btn,"disabled")=="true","aria_label":_safe(btn,"aria-label"),"type":_safe(btn,"type") or "button"})
            except: continue
        for inp in driver.find_elements(By.CSS_SELECTOR,"input[type='button'],input[type='submit'],input[type='reset']"):
            try:
                if not inp.is_displayed(): continue
                items.append({"element_type":"input_button","text":_safe(inp,"value"),"selector":_selector(inp),"description":_desc(inp),"type":_safe(inp,"type")})
            except: continue
        return items

    def extract_navigation(self, driver: WebDriver) -> list:
        items = []; seen = set()
        for a in driver.find_elements(By.TAG_NAME, "a"):
            try:
                if not a.is_displayed(): continue
                href = _safe(a,"href")
                if not href or href in seen or any(href.startswith(p) for p in ["javascript:","mailto:"]): continue
                seen.add(href)
                items.append({"element_type":"link","text":a.text.strip()[:80],"href":href,"selector":_selector(a),"description":_desc(a),"target":_safe(a,"target"),"is_external":self._ext(driver.current_url,href)})
            except: continue
        return items

    def extract_forms(self, driver: WebDriver) -> list:
        forms = []
        for i, form in enumerate(driver.find_elements(By.TAG_NAME, "form")):
            try:
                fd = {"element_type":"form","form_index":i,"action":_safe(form,"action"),"method":_safe(form,"method") or "GET","selector":_selector(form),"fields":[],"submit_buttons":[]}
                for inp in form.find_elements(By.TAG_NAME, "input"):
                    t = _safe(inp,"type") or "text"
                    if t == "hidden": continue
                    if t in ["submit","button","reset"]:
                        fd["submit_buttons"].append({"type":t,"value":_safe(inp,"value"),"selector":_selector(inp)}); continue
                    fd["fields"].append({"element_type":f"input_{t}","input_type":t,"name":_safe(inp,"name"),"id":_safe(inp,"id"),"placeholder":_safe(inp,"placeholder"),"required":_safe(inp,"required") in ["true",""],"selector":_selector(inp),"label":self._lbl(driver,inp),"description":_desc(inp),"validation":{k:v for k,v in {"minlength":_safe(inp,"minlength"),"maxlength":_safe(inp,"maxlength"),"pattern":_safe(inp,"pattern"),"min":_safe(inp,"min"),"max":_safe(inp,"max")}.items() if v}})
                for ta in form.find_elements(By.TAG_NAME, "textarea"):
                    fd["fields"].append({"element_type":"textarea","name":_safe(ta,"name"),"placeholder":_safe(ta,"placeholder"),"required":_safe(ta,"required") in ["true",""],"selector":_selector(ta),"label":self._lbl(driver,ta),"description":_desc(ta)})
                for sel in form.find_elements(By.TAG_NAME, "select"):
                    opts = [{"text":o.text.strip(),"value":_safe(o,"value")} for o in sel.find_elements(By.TAG_NAME,"option")]
                    fd["fields"].append({"element_type":"select","name":_safe(sel,"name"),"required":_safe(sel,"required") in ["true",""],"selector":_selector(sel),"label":self._lbl(driver,sel),"options":opts[:20],"description":_desc(sel)})
                for btn in form.find_elements(By.CSS_SELECTOR,"button[type='submit'],button:not([type])"):
                    fd["submit_buttons"].append({"type":"submit","text":btn.text.strip(),"selector":_selector(btn)})
                forms.append(fd)
            except: continue
        return forms

    def extract_media(self, driver: WebDriver) -> list:
        items = []
        for img in driver.find_elements(By.TAG_NAME, "img"):
            try:
                if not img.is_displayed(): continue
                items.append({"element_type":"image","src":_safe(img,"src"),"alt":_safe(img,"alt"),"has_alt":bool(_safe(img,"alt")),"selector":_selector(img)})
            except: continue
        return items

    def extract_content_structure(self, driver: WebDriver) -> list:
        items = []
        for tag in ["h1","h2","h3","h4"]:
            for h in driver.find_elements(By.TAG_NAME, tag):
                try:
                    text = h.text.strip()
                    if text: items.append({"element_type":"heading","level":tag,"text":text[:100],"selector":_selector(h)})
                except: continue
        return items

    def extract_tables(self, driver: WebDriver) -> list:
        items = []
        for i, tbl in enumerate(driver.find_elements(By.TAG_NAME, "table")):
            try:
                headers = [th.text.strip() for th in tbl.find_elements(By.TAG_NAME,"th")]
                rows    = len(tbl.find_elements(By.TAG_NAME,"tr"))
                items.append({"element_type":"table","table_index":i,"headers":headers,"row_count":rows,"selector":_selector(tbl)})
            except: continue
        return items

    def _lbl(self, driver, el):
        try:
            el_id = _safe(el,"id")
            if el_id:
                ls = driver.find_elements(By.CSS_SELECTOR, f"label[for='{el_id}']")
                if ls: return ls[0].text.strip()
            p = el.find_element(By.XPATH, "..")
            if p.tag_name == "label": return p.text.strip()[:60]
        except: pass
        return ""

    def _ext(self, current, href):
        try:
            from urllib.parse import urlparse
            return urlparse(href).netloc not in ("", urlparse(current).netloc)
        except: return False