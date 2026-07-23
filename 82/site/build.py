from pathlib import Path
import json

ROOT = Path(__file__).parent
NAV = [("index.html", "首页"), ("menu.html", "招牌产品"), ("about.html", "品牌故事"), ("stores.html", "门店空间"), ("news.html", "食味手记")]
PRODUCTS = [
    ("dry-chili.webp", "招牌干海椒抄手", "干香辣", "干海椒的焦香先到，拌开以后越吃越香。", "dry spicy"),
    ("green-pepper.webp", "藤椒抄手", "椒麻鲜", "藤椒清香带着轻盈麻感，鲜爽不闷。", "numbing fresh"),
    ("hotpot.webp", "火锅抄手", "红油香", "熟悉的火锅香气，热辣浓郁又满足。", "spicy rich"),
    ("sour-spicy.webp", "酸辣抄手", "酸辣味", "酸香先开胃，随后是一口利落的辣。", "sour spicy"),
    ("tomato-beef.webp", "番茄牛腩抄手", "浓汤味", "番茄酸甜融进牛腩炖香，汤底温厚。", "soup rich"),
    ("chicken-bamboo.webp", "土鸡竹荪抄手", "清炖味", "土鸡鲜香与竹荪清润，温和耐吃。", "soup fresh"),
    ("bamboo-beef.webp", "烟笋牛腩抄手", "川味炖香", "烟笋的山野香气，衬出牛腩的浓郁。", "rich spicy"),
    ("mushroom-chicken.webp", "姬松茸炖鸡抄手", "菌汤味", "菌菇香融入鸡汤，鲜而不厚重。", "soup fresh"),
    ("pickled-fish.webp", "酸菜鱼抄手", "酸鲜味", "酸菜爽口、鱼汤鲜美，层次清楚。", "sour fresh"),
    ("classic.webp", "传统水饺味抄手", "经典味", "朴实熟悉的一碗，怎么吃都安心。", "classic fresh"),
]
TASTES = [
    ("dry", "干香辣", "招牌干海椒", "dry-chili.webp", "焦香、鲜辣、拌开更香", "不靠厚重汤底，干海椒的香气牢牢裹住每一只抄手。"),
    ("numbing", "椒麻鲜", "藤椒清香", "green-pepper.webp", "清香、微麻、入口鲜爽", "藤椒的清香先钻进鼻子，随后是一阵轻盈的麻。"),
    ("sour", "酸辣味", "一口开胃", "sour-spicy.webp", "酸香、鲜辣、利落开胃", "酸得清醒，辣得舒服，适合想吃一碗痛快的时候。"),
    ("soup", "暖汤味", "炖香入味", "tomato-beef.webp", "温厚、浓鲜、热汤暖胃", "番茄、牛腩、鸡汤与菌菇，把抄手变成一顿暖和的饭。"),
]

def nav(current):
    links = "".join(f'<a class="{"current" if href == current else ""}" href="{href}">{label}</a>' for href, label in NAV)
    return f'''<header class="site-head"><div class="wrap head-inner"><a class="logo" href="index.html"><img src="../assets/brand-mark.png" alt="八二小区抄手"><span><b>八二小区抄手</b><small>PEPPER WONTON · CHENGDU</small></span></a><nav class="nav" aria-label="主导航">{links}<a class="nav-cta {"current" if current == "partner.html" else ""}" href="partner.html">合作加盟</a></nav><button class="hamburger" type="button" aria-label="打开导航" aria-expanded="false"><i></i><i></i><i></i></button></div></header>'''


def footer():
    return '''<footer class="site-foot"><div class="wrap"><div class="foot-top"><div class="foot-brand"><img src="../assets/brand-mark.png" alt="八二小区抄手"><div><strong>一碗热抄手，吃到西南味。</strong><p>从成都建设巷出发，把麻、辣、酸、鲜认真包进每一碗。</p></div></div><a class="foot-cta" href="menu.html">去选今天这一碗 <span>↗</span></a></div><div class="foot-links"><div><h4>好吃的</h4><a href="menu.html">招牌产品</a><a href="news.html">食味手记</a></div><div><h4>认识八二</h4><a href="about.html">品牌故事</a><a href="stores.html">门店空间</a></div><div><h4>一起开店</h4><a href="partner.html">合作加盟</a><span>合作有风险，决策需谨慎</span></div></div><div class="foot-bottom"><span>© 2026 八二小区抄手</span><span>PEPPER WONTON · CHENGDU</span></div></div></footer>'''


def layout(title, description, current, body, structured=None):
    schema = f'<script type="application/ld+json">{json.dumps(structured, ensure_ascii=False, separators=(",", ":"))}</script>' if structured else ""
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="{description}"><meta name="theme-color" content="#a63828"><title>{title}</title><link rel="stylesheet" href="styles.css">{schema}</head><body>{nav(current)}<main>{body}</main>{footer()}<script src="app.js"></script></body></html>'''


def taste_selector(compact=False):
    buttons = "".join(f'<button class="taste-tab {"active" if i == 0 else ""}" type="button" data-taste="{key}"><span>0{i + 1}</span>{label}</button>' for i, (key, label, *_rest) in enumerate(TASTES))
    panels = "".join(f'''<article class="taste-panel {"active" if i == 0 else ""}" data-taste-panel="{key}"><div class="taste-photo"><img src="../assets/products/{image}" alt="{name}"><b>{label}</b></div><div class="taste-copy"><p class="eyebrow">{label} · {profile}</p><h3>{name}</h3><p>{description}</p><a href="menu.html">看看更多口味 <span>↗</span></a></div></article>''' for i, (key, label, name, image, profile, description) in enumerate(TASTES))
    return f'<div class="taste-selector{" compact" if compact else ""}"><div class="taste-tabs" role="tablist">{buttons}</div><div class="taste-panels">{panels}</div></div>'


def product_cards():
    return "".join(f'''<article class="menu-card reveal" data-flavor="{tags}"><div class="menu-photo"><img src="../assets/products/{image}" alt="{name}"><span>{flavor}</span></div><div class="menu-copy"><h3>{name}</h3><p>{description}</p></div></article>''' for image, name, flavor, description, tags in PRODUCTS)


home = f'''<section class="home-hero"><div class="wrap hero-grid"><div class="hero-copy reveal"><p class="eyebrow">成都建设巷 · 现包热抄手</p><h1>一口抄手，<br><em>满口西南。</em></h1><p class="hero-lead">麻得清香，辣得过瘾，酸得开胃，汤也要炖得鲜。今天想吃哪一味，八二都给你热腾腾地端上来。</p><div class="hero-actions"><a class="button primary" href="#taste">选今天这一碗</a><a class="text-link" href="about.html">从建设巷说起 <span>↗</span></a></div></div><div class="hero-visual reveal"><div class="hero-dish"><img src="../assets/products/dry-chili.webp" alt="招牌干海椒抄手"></div><div class="hero-stamp"><span>招牌</span><b>干海椒</b><small>拌开就香</small></div><p class="hero-side">PEPPER<br>WONTON<br>CHENGDU</p></div></div><div class="flavor-marquee" aria-hidden="true"><span>麻 · 辣 · 酸 · 鲜 · 现包 · 热乎 · 成都味 · </span><span>麻 · 辣 · 酸 · 鲜 · 现包 · 热乎 · 成都味 · </span></div></section>
<section class="section taste-section" id="taste"><div class="wrap"><header class="section-head reveal"><div><p class="eyebrow">Choose Your Flavor</p><h2>先选味道，<br>再选这一碗。</h2></div><p>西南味不只有辣。清香的麻、利落的酸、温厚的汤，每一种都有自己的脾气。</p></header>{taste_selector()}</div></section>
<section class="section craft-section"><div class="wrap craft-layout"><div class="craft-image reveal"><img src="assets/fresh-made-sign.webp" alt="八二小区抄手现包门店"><span>每天现包 · 趁热上桌</span></div><div class="craft-copy reveal"><p class="eyebrow">Freshly Wrapped</p><h2>好吃这件事，<br>藏不住。</h2><p>面皮的软韧、馅心的鲜香、汤底的热气，都在明档里看得见。包好一只，煮好一碗，香气就是最直接的招呼。</p><div class="craft-notes"><span><b>01</b>现包</span><span><b>02</b>现煮</span><span><b>03</b>现拌</span></div><a class="button outline" href="stores.html">走进门店看看</a></div></div></section>
<section class="section origin-section"><div class="wrap origin-grid"><div class="origin-copy reveal"><p class="eyebrow">Born in Chengdu</p><h2>从建设巷走出来，<br>身上自然带着成都味。</h2><p>这里有街巷的热闹，也有一日三餐的认真。八二想做的很简单：把一碗抄手做出更多西南风味，让熟悉的食物一直有新鲜感。</p><a class="text-link" href="about.html">认识八二小区抄手 <span>↗</span></a></div><div class="origin-art reveal"><img src="assets/chengdu-wall.webp" alt="八二小区抄手成都墙画视觉"></div></div></section>
<section class="section note-section"><div class="wrap"><header class="section-head reveal"><div><p class="eyebrow">Bite Notes</p><h2>关于好吃，<br>我们还有很多想说。</h2></div><a class="text-link" href="news.html">读更多食味手记 <span>↗</span></a></header><div class="note-grid"><a class="note-card feature reveal" href="news.html"><span>01 · 味道</span><h3>西南味，不只是“辣”</h3><p>藤椒的清香、酸菜的爽口、菌汤的温润，都能成为一碗抄手的主角。</p><b>继续读 ↗</b></a><a class="note-card reveal" href="news.html"><span>02 · 手艺</span><h3>为什么要趁热吃？</h3><p>刚出锅时，皮、馅、汤底的口感最有层次。</p><b>继续读 ↗</b></a><a class="note-card image reveal" href="stores.html"><img src="assets/appetite-illustration.webp" alt="八二小区抄手品牌插画"><div><span>03 · 门店</span><h3>在店里，看见成都的热闹</h3></div></a></div></div></section>
<section class="join-banner"><div class="wrap join-inner"><div><p class="eyebrow">Bring It To Your City</p><h2>想把这碗成都味，<br>带到你的城市？</h2></div><a class="button cream" href="partner.html">了解合作加盟</a></div></section>'''

menu = f'''<section class="page-hero menu-hero"><div class="wrap"><p class="eyebrow">Signature Menu</p><h1>十种味道，<br><em>总有一碗对胃口。</em></h1><p>想吃干香、椒麻、酸辣，还是一碗暖汤？先跟着味道选，再认识每一款抄手。</p></div></section><section class="section menu-picker"><div class="wrap">{taste_selector(compact=True)}</div></section><section class="section all-menu"><div class="wrap"><header class="section-head"><div><p class="eyebrow">All Flavors</p><h2>十碗西南味，<br>一次看个够。</h2></div><div class="filters" aria-label="产品筛选"><button class="active" data-filter="all">全部</button><button data-filter="spicy">香辣</button><button data-filter="fresh">鲜香</button><button data-filter="sour">酸爽</button><button data-filter="soup">暖汤</button></div></header><div class="menu-grid">{product_cards()}</div></div></section>'''

about = '''<section class="page-hero story-hero"><div class="wrap"><p class="eyebrow">Our Story</p><h1>一碗抄手，<br><em>一座城的日常。</em></h1><p>八二小区抄手从成都建设巷出发。我们喜欢这里的热闹，也相信真正留住人的，是一口一口吃出来的味道。</p></div></section><section class="section story-intro"><div class="wrap story-spread"><div class="story-photo reveal"><img src="assets/chengdu-wall.webp" alt="成都城市文化墙画"></div><div class="story-text reveal"><p class="eyebrow">Chengdu, Everyday</p><h2>成都的好吃，<br>从来不端着。</h2><p>它可以是下班后的一碗热汤，也可以是朋友见面时的一盘红油。八二把这种松弛、热情又讲究的日常，放进产品和门店里。</p><blockquote>“让一碗熟悉的抄手，长出更多西南味道。”</blockquote></div></div></section><section class="section values-section"><div class="wrap"><header class="section-head"><div><p class="eyebrow">What We Care About</p><h2>我们在意的，<br>都在这一碗里。</h2></div></header><div class="value-list"><article><span>01</span><h3>味道有记忆</h3><p>每一款先说清楚是什么味，再让香气和口感留下印象。</p></article><article><span>02</span><h3>出锅要热乎</h3><p>现包、现煮、现拌，让皮、馅与汤底在最好吃的时候见面。</p></article><article><span>03</span><h3>成都不只一种表情</h3><p>既有街巷烟火，也有清楚利落的现代门店体验。</p></article></div></div></section><section class="section brand-mark-section"><div class="wrap brand-mark-grid"><img src="../assets/brand-mark.png" alt="八二小区抄手品牌标志"><div><p class="eyebrow">Meet The Mark</p><h2>一张亲切的脸，<br>一句成都的招呼。</h2><p>品牌标志保留了市井亲切感，也让八二在热闹街巷里一眼就能被认出来。</p></div></div></section>'''

stores = '''<section class="page-hero store-hero"><div class="wrap"><p class="eyebrow">Store Experience</p><h1>走近一点，<br><em>香气已经在招呼你。</em></h1><p>清楚的门头、热闹的明档、好选的菜单，让进店到端碗的每一步都简单、热乎。</p></div></section><section class="section store-gallery"><div class="wrap"><div class="store-feature reveal"><img src="assets/fresh-made-sign.webp" alt="八二小区抄手现包门店视觉"><div><span>OPEN KITCHEN</span><h2>包、煮、拌，<br>都在眼前发生。</h2><p>等待的几分钟里，看得见手艺，也闻得到刚出锅的香气。</p></div></div><div class="store-detail reveal"><div><img src="assets/chengdu-wall.webp" alt="八二小区抄手成都墙画"><span>成都街巷的热闹</span></div><div class="store-words"><p class="eyebrow">Easy To Choose</p><h3>看得懂，选得快。</h3><p>味型清楚、产品直观。香辣、椒麻、酸鲜、浓汤，今天想吃什么不必猜。</p></div></div></div></section><section class="section store-principles"><div class="wrap"><header class="section-head"><div><p class="eyebrow">Three First Impressions</p><h2>一家八二门店，<br>先给你这三种感受。</h2></div></header><div class="principle-row"><article><b>01</b><h3>好认</h3><p>远远看到招牌，就知道这里有一碗成都味。</p></article><article><b>02</b><h3>好看</h3><p>现包明档和热气，让好吃变得看得见。</p></article><article><b>03</b><h3>好选</h3><p>跟着味型点单，很快找到今天想吃的。</p></article></div></div></section>'''

news = '''<section class="page-hero notes-hero"><div class="wrap"><p class="eyebrow">Bite Notes</p><h1>吃一碗，<br><em>也读懂一碗。</em></h1><p>从味型、食材到现包日常，聊聊一碗抄手为什么让人惦记。</p></div></section><section class="section notes-list"><div class="wrap"><article class="editorial feature reveal"><div class="editorial-image"><img src="../assets/products/green-pepper.webp" alt="藤椒抄手"></div><div class="editorial-copy"><span>味道 · 西南风味</span><h2>西南味，<br>不只是“辣”</h2><p>藤椒带来清香和麻，酸菜带来爽口和鲜，菌汤则让一碗抄手变得温润。味道有很多条路，辣只是其中一条。</p><a href="menu.html">按味型选一碗 <b>↗</b></a></div></article><article class="editorial reveal"><div class="editorial-copy"><span>手艺 · 现包现煮</span><h2>趁热，才是抄手最好吃的时刻</h2><p>刚起锅时，面皮软韧、馅心鲜香，汤和红油也正好裹住每一道褶。所谓热乎，不只是温度，也是完整的口感。</p></div><div class="editorial-image"><img src="assets/fresh-made-sign.webp" alt="现包现煮的门店场景"></div></article><article class="editorial feature reverse reveal"><div class="editorial-image"><img src="../assets/products/tomato-beef.webp" alt="番茄牛腩抄手"></div><div class="editorial-copy"><span>一碗饭 · 暖汤系列</span><h2>想吃暖和一点，<br>就选一碗有炖香的</h2><p>番茄牛腩、土鸡竹荪、姬松茸炖鸡，把抄手和一碗汤饭的满足感放在一起。</p><a href="menu.html">看看暖汤口味 <b>↗</b></a></div></article></div></section>'''

partner = '''<section class="page-hero partner-hero"><div class="wrap"><p class="eyebrow">Partnership</p><h1>把一碗成都味，<br><em>带到更多城市。</em></h1><p>如果你认同产品第一、现包现卖和西南特色口味，欢迎进一步了解八二小区抄手。</p><a class="button primary" href="#process">了解合作流程</a></div></section><section class="section partner-intro"><div class="wrap partner-manifesto"><div><p class="eyebrow">What We Build Together</p><h2>合作的起点，<br>是一碗真的好吃。</h2></div><p>品牌形象、门店设计和运营方法都很重要，但最终要回到产品。我们围绕味型、出品、门店体验与日常经营逐项沟通。</p></div></section><section class="section support-section"><div class="wrap"><div class="support-grid"><article><span>01 · BRAND</span><h3>品牌与门店形象</h3><p>围绕门头、空间、菜单和物料，建立清楚统一的品牌体验。</p></article><article><span>02 · PRODUCT</span><h3>产品与出品学习</h3><p>围绕核心味型、操作流程和出品稳定开展学习与检查。</p></article><article><span>03 · OPENING</span><h3>筹备与开业协同</h3><p>按节点沟通选址评估、设计、培训、物料与开业准备。</p></article><article><span>04 · OPERATION</span><h3>日常经营沟通</h3><p>具体支持范围、频次与条件，以双方最终签署的协议为准。</p></article></div></div></section><section class="section process-section" id="process"><div class="wrap"><header class="section-head"><div><p class="eyebrow">Standard Process</p><h2>从彼此了解，<br>到认真开好一家店。</h2></div></header><div class="process-line"><article><b>01</b><h3>了解品牌</h3><p>认识产品、门店与合作方向。</p></article><article><b>02</b><h3>提交意向</h3><p>提供城市与项目基本情况。</p></article><article><b>03</b><h3>双方评估</h3><p>核验资格、区域和项目条件。</p></article><article><b>04</b><h3>书面确认</h3><p>通过合同明确双方权利义务。</p></article></div><div class="risk"><strong>风险提示</strong><p>合作经营受选址、市场、管理、成本等多重因素影响，不承诺收益、回本周期或经营结果。请充分评估并审慎决策。</p></div></div></section>'''

schema = {"@context": "https://schema.org", "@type": "Restaurant", "name": "八二小区抄手", "servesCuisine": ["川味", "抄手", "西南风味"], "description": "成都建设巷走出来的西南风味抄手品牌。"}
pages = {
    "index.html": layout("八二小区抄手｜一口抄手，满口西南", "八二小区抄手从成都建设巷出发，以现包热抄手和麻、辣、酸、鲜的西南特色口味为核心。", "index.html", home, schema),
    "menu.html": layout("招牌产品｜八二小区抄手", "查看八二小区抄手十种西南味型产品，从干香辣、椒麻鲜、酸辣到暖汤口味。", "menu.html", menu),
    "about.html": layout("品牌故事｜八二小区抄手", "了解八二小区抄手从成都建设巷出发的品牌故事。", "about.html", about),
    "stores.html": layout("门店空间｜八二小区抄手", "走进八二小区抄手门店，感受清楚门头、明档现包与成都街巷氛围。", "stores.html", stores),
    "news.html": layout("食味手记｜八二小区抄手", "阅读八二小区抄手关于西南味型、现包手艺和暖汤产品的食味手记。", "news.html", news),
    "partner.html": layout("合作加盟｜八二小区抄手", "了解八二小区抄手的合作方向、支持内容、标准流程与风险提示。", "partner.html", partner),
}
for name, content in pages.items():
    (ROOT / name).write_text(content, encoding="utf-8")
print("generated", len(pages), "pages")
