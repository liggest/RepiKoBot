#import "@preview/cuti:0.3.0": show-cn-fakebold

#import "md_base.typ": render-md, maybe-image, make-md-quote

#let maybe-image-md(path, ..args) = maybe-image(path, ..args)

#let md-text-style(doc, color: luma(32)) = {
  set text(font: ((name: "Inria Serif", covers: "latin-in-cjk"),"Noto Sans CJK SC"), lang: "zh", size: 8pt, fill: color)
  doc
}

#let md-init(doc, width: 5in, text-style: md-text-style) = {
  // page
  // set page(width: width, height: auto, margin: 8pt)
  // font
  // set text(font: ((name: "Inria Serif", covers: "latin-in-cjk"),"Noto Sans CJK SC"), lang: "zh", size: 8pt, fill: luma(32))
  show: text-style
  set par(spacing: 0.5em)
  // cuti
  show: show-cn-fakebold
  // heading 4, 5, 6
  show heading.where(level: 4) : set text(size: 10pt)
  show heading.where(level: 5) : set text(size: 9pt)
  show heading.where(level: 6) : set text(size: 8pt)
  // code
  show raw : set text(font: ("Cascadia Mono", "Noto Sans CJK SC"))
  show raw.where(block: true) : block.with(
    fill: luma(242),
    inset: 8pt,
    radius: 4pt,
    width: 100%
  )
  show raw.where(block: false) : box.with(
    fill: luma(242),
    inset: (x: 3pt, y: 0pt),
    outset: (y: 3pt),
    radius: 2pt,
  )
  // link
  show link: text.with(fill: rgb(17, 86, 142))
  // math
  show math.equation: set text(font: "Cambria Math")
  // enum
  set enum(numbering: n => text(numbering("1.", n), font: "libertinus serif"))
  doc
}

#let brighter-block-quote = it => block(text(it), 
  stroke: (left: 1.5pt + luma(64)), fill: luma(242), inset: (right: 2pt, rest: 4pt), width: 100%
)

#let brighter-md-text = md-text-style.with(color: luma(96))

#let system-init = md-init.with(text-style: brighter-md-text)
#let reasoning-init = system-init

#let text-avatar-colors(num) = color.hsl(10deg * num, 64%, 48%)

#let text-to-color(content) = text-avatar-colors(
  calc.rem(content.codepoints().map(str.to-unicode).sum(), 36)
)

#let text-avatar-color(content, color: none) = if color == none { 
  text-to-color(content) 
} else { 
  color 
}

#let text-avatar(content, color: none) = circle(
  width: 20pt, fill: text-avatar-color(content, color: color)
)[
  #align(center + horizon)[
    #text(content.first(), 
      font: ((name: "Inria Serif", covers: "latin-in-cjk"),"Noto Sans CJK SC"), 
      lang: "zh", fill: luma(255), weight: "bold"
    )
  ]
]

#let system-block(md-text) = block(stroke: (1pt + luma(128)), inset: 4pt, radius: 4pt)[
  #render-md(md-text, image: maybe-image-md, init: system-init, width: auto)
]

#let user-block(md-text) = block(outset: (top: 2pt, bottom: 2pt), inset: 4pt, fill: rgb(239, 246, 255), radius: 4pt)[
  #set align(left)
  #render-md(md-text, image: maybe-image-md, init: md-init, width: auto)
]

#let reasoning-block(md-text) = block(stroke: (left: 1pt + luma(128)), inset: (left: 4pt, top: 2pt, bottom: 2pt))[
  #render-md(md-text, 
    image: maybe-image-md, quote: make-md-quote(brighter-block-quote), 
    init: reasoning-init, width: auto
  )
]

#let tool-content(content, name: none) = {
  if content.find(regex(`\\u([0-9a-fA-F]{4})`.text)) != none {
    // \uxxxx to unicode
    content = json.encode(json(bytes(content)), pretty: false)
  }
  // exclude leading html tags
  // (?m) => multiline flag
  let start_idx = content.position(regex(`(?m)^[^<]`.text))
  // wrap content with code block
  if start_idx != none {
    content = content.slice(0, start_idx) + "```\n" + content.slice(start_idx, none) + "\n```"
  } else {
    content = "```\n" + content + "\n```"
  }
  if name != none {
    content = "🛠️" + name + "\n\n" + content
  }
  content
}

#let tool-call-block(content) = block(
  inset: (right: 4pt, bottom: -0.7em),
  outset: (bottom: 0.7em),
  spacing: 0.7em
)[
  #render-md(content,  //-----\n\n
    image: maybe-image-md, quote: make-md-quote(brighter-block-quote),
    init: reasoning-init, width: auto
  )
]

#let tool-call-blocks(tool-calls) = {
  if tool-calls == none {
    return
  }
  for call in tool-calls {
    tool-call-block(
      tool-content(call.function.arguments, name:call.function.name)
    )
  }
}

#let tool-result-block(md-text) = block(
  stroke: (left: (paint: luma(128), thickness: 1pt)),
  inset: (right: 4pt, left: 4pt, bottom: 2pt),
  radius: (bottom-left: 4pt),
)[
  #render-md(md-text,
    image: maybe-image-md, quote: make-md-quote(brighter-block-quote),
    init: reasoning-init, width: auto
  )
]

#let assistant-block(md-text) = render-md(md-text, image: maybe-image-md, init: md-init, width: auto)

#let error-color = color.hsl(0deg, 50%, 50%)

#let error-block(md-text) = block(stroke: (1pt + error-color), inset: 4pt, radius: 4pt)[
  #render-md(md-text, image: maybe-image-md, init: md-init, width: auto)
]

#let message(data) = {
  // let x = (role: "assistant", content: "123")
  let role = data.at("role", default: "assistant")
  let left-grid = if role == "system" [
    #v(-4pt)
    #text-avatar("System")
  ] else if role == "assistant" [
    #v(-4pt)
    #text-avatar("Bot")
  ] else if role == "error" [
    #v(-1pt)
    #text-avatar("!", color: error-color)
  ] else []
  let right-grid = if role == "user" [
    #v(-4pt)
    #text-avatar("User")
  ] else []
  let mid-grid = [
    #block(width: 4in, outset: (top: 4pt, bottom: 4pt), inset: 2pt)[
      #if "reasoning_content" in data {
        reasoning-block(data.at("reasoning_content", default: "None"))
      }
      #let content = data.at("content", default: "None")
      #if role == "system" {
        system-block(content)
      } else if role == "user" {
        // make user content more md-like by adding extra newlines
        user-block(content.replace("\n", "\n\n"))
        // align(left, user-block(content))
      } else if role == "assistant" {
        // trim assistant content at start
        assistant-block(content.trim(at: start))
      } else if role == "tool" {
        tool-result-block(tool-content(content))
      } else if role == "error" {
        error-block(content)
      }
      #if "tool_calls" in data {
        tool-call-blocks(data.at("tool_calls", default: none))
      }
    ]
  ]

  let row = grid(left-grid, mid-grid, right-grid, columns: (20pt, auto, 20pt), column-gutter: 4pt)

  if role == "user" {
    align(right, row)
  } else {
    row
  }
}

#let messages(data) = {
  for msg in data {
    message(msg)
  }
}
