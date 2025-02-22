
import asyncio
from pathlib import Path

from repiko.msg.part import Image
from repiko.msg.content import Content
from repiko.msg.util import CQunescape
from repiko.module.img.typ import typ_file2png, default_font_paths, default_root_path

from LSparser import Command, Events, ParseResult #, OPT

def images_gen(data: bytes | list[bytes]):
    if isinstance(data, bytes):
        yield Image(data)
    else:
        for d in data:
            yield Image(d)

# Command("-ttest")

# @Events.onCmd("ttest")
# def ttest(_):
#     return [Image(typ_file2png("typ/temp.typ", None, default_font_paths(), 144, {
#         "width": "5"
#     }))]

TemplateBase = Path("typ/template")
template_map = {
    "typst": "typ_temp.typ", 
    "typmd": "md_temp.typ", 
    "typtex": "tex_temp.typ", 
}

Command("typst").names("typ")
Command("typmd").names("tmd", "md", "markdown")
Command("typtex").names("ttex")

@Events.onCmd("typst")
@Events.onCmd("typmd")
@Events.onCmd("typtex")
async def typst(pr: ParseResult):
    if not pr.params:
        return ["空空如也…"]
    content = CQunescape(Content(pr.paramStr).plainText)
    template = template_map.get(pr._cmd.name)
    assert template, "模板不存在"
    template_data = {"content": content, "content_type": "str"}
    return Content(*images_gen(
        await asyncio.to_thread(typ_file2png, TemplateBase / template, default_font_paths(), root=default_root_path(), ppi=144, data=template_data)
    ))

# async def typmd(pr: ParseResult):
#     if not pr.params:
#         return ["空空如也…"]
#     content = CQunescape(Content(pr.paramStr).plainText)
#     typ_content = """
#     #import "base/md_base.typ": render-md
#     #let md_content = sys.inputs.at("content", default: "")
#     #render-md(md_content)
#     """
#     return [Image(
#        await asyncio.to_thread(typ_str2png, typ_content, None, default_font_paths(), ppi=144, data={"content": content})
#     )]

# async def typtex(pr: ParseResult):
#     if not pr.params:
#         return ["空空如也…"]
#     content = CQunescape(Content(pr.paramStr).plainText)
#     typ_content = """
#     #import "base/tex_base.typ": render-tex
#     #let tex_content = sys.inputs.at("content", default: "")
#     #render-tex(tex_content)
#     """
#     return [Image(
#        await asyncio.to_thread(typ_str2png, typ_content, None, default_font_paths(), 144, {"content": content})
#     )]

@Events.onCmd.error("typst")
@Events.onCmd.error("typmd")
@Events.onCmd.error("typtex")
def texError(pr:ParseResult, e:Exception):
    if isinstance(e, RuntimeError):
        root = str(Path.cwd().absolute())
        return [" ".join(e.args).replace(root, ".")]
    raise e
