#import "@preview/cmarker:0.1.6"
#import "@preview/mitex:0.2.5": mitex
#import "@preview/cuti:0.3.0": show-cn-fakebold

#let init(width: 5in, doc) = {
  // page
  set page(width: width, height: auto, margin: 8pt)
  // font
  set text(font: ((name: "Inria Serif", covers: "latin-in-cjk"), "LXGW WenKai"), lang: "zh")
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

#let md-block-quote = it => block(text(it), stroke: (left: 1.5pt + luma(64)), fill: luma(242), inset: (right: 2pt, rest: 4pt), width: 100%)

#let make-md-quote(quote: quote, block_quote) = (block: false, ..rest) => if block { block_quote(..rest) } else { quote(..rest) }

#let md-quote = make-md-quote(md-block-quote)

#let maybe-image(path, ..args) = context {
  let path-label = label(path)
   let first-time = query((context {}).func()).len() == 0
   if first-time or query(path-label).len() > 0 {
    [#image(path, ..args)#path-label]
  } else {
    rect(width: 12em, height: 3em, fill: luma(242), stroke: 1pt)[
      #set align(center + horizon)
      #sym.crossmark.heavy Image Not Found #sym.crossmark.heavy
    ]
  }
}

#let maybe-image-md(path, alt: none) = maybe-image(path, alt: alt)

#let tag-attrs(attrs) = {
  attrs.pairs().map(((key, value)) => {
    key + "=\"" + value + "\""
  }).join(" ")
}

#let tag(name: "div", attrs: (:), inner) = {
  "<" + name + " " + tag-attrs(attrs) + ">" + inner + "</" + name + ">"
}

#let md-svg(attrs, body) = {
  image(bytes(tag(name: "svg", attrs: attrs, body)))
}

#let to-inches(value) = {
  if type(value) == str {
    value = float(value)
  }
  if type(value) == float or type(value) == int{
    value * 1in
  } else if value == none {
    auto
  } else {
    value
  }
}

#let render-md(
  md-text,
  width: 5in,
  init: init,
  image: (path, alt: none) => maybe-image(path, alt: alt),
  quote: md-quote,
  scope: (:),
  html: (svg: ("raw-text", md-svg)),
  smart-punctuation: false,
) = {
  let args = sys.inputs
  width = to-inches(args.at("width", default: width))
  show: init.with(width: width)
  cmarker.render(md-text, 
    math: mitex, 
    scope: scope + (image: image, quote: quote),
    html: html,
    smart-punctuation: smart-punctuation
  )
}
