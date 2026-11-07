# LinkedIn post

**Image:** `docs/assets/linkedin_poster.png` (portrait 4:5, 2160 x 2700, the format that fills the most of a phone
screen in the feed), rebuilt from the paper's figures and `data/processed/metrics.json` by
`scripts/make_linkedin_poster.py` (`make poster`).

**Alt text for the image:** Poster for the working paper "Twelve Views of Thai Tourism". Four research questions,
each with its row of charts drawn from synthetic data: who visits and when (unit chart, radial spiral,
streamgraph, ridgeline plot); where visitors go (Sankey diagram, chord diagram, edge bundling); where the money
goes (circle packing, sunburst, beeswarm); what kinds of travellers there are (parallel coordinates, t-SNE
embedding map). Below, the structure planted in the data and recovered by the views: seasonal profile r = 0.998,
median length of stay within 0.32 nights, destination preferences within 0.37 percentage points, six traveller
personas found again with an adjusted Rand index of 0.85. All data are synthetic.

Every number below is in the paper and on the poster. Post the links as the first comment.

---

## Post (English, about 2,800 characters)

Tourism data come in many shapes. Most tourism reports use two charts.

A monthly arrivals series is a cycle. Market-to-destination travel is a flow. Spending is a hierarchy. Provinces visited on the same trip form a network. A visitor survey is a cloud of individuals. Squeeze them into bar and line charts and the structure you care about has to be dug back out of tables.

So my new working paper asks two questions:
1. Which visual idiom fits which tourism question?
2. Does each view actually show the structure it claims to show?

Four questions, twelve views, each chosen for the shape of the data its question needs:
• Who visits, and when? Unit chart, radial spiral, streamgraph, ridgeline plot
• Where do visitors go? Sankey diagram, chord diagram, hierarchical edge bundling
• Where does the money go? Circle packing, sunburst, beeswarm
• What kinds of travellers are there? Parallel coordinates, t-SNE embedding map

The second is the hard one: with official data you never know the true structure. So I planted it in ten synthetic datasets, 2010 to 2025: a seasonal profile, a pandemic collapse, destination preferences, a Bangkok hub for onward travel, concentrated revenue and six hidden traveller personas. Each view gets a companion statistic that measures what comes back.

What the views recovered:
→ the seasonal profile, at r = 0.998 (radial spiral)
→ median length of stay, within 0.32 nights on average (ridgeline plot)
→ destination preferences, within 0.37 percentage points (Sankey diagram)
→ the six personas, with an adjusted Rand index of 0.85 (embedding map)
Each remaining error has a known source: injected noise, rounding, or whole nights.

Two lessons:
• One question often needs more than one scale. The Sankey shows where each market goes, the chord diagram which destinations feed each other, edge bundling which provinces are visited together. None replaces the others.
• Expressive views cost precision. Angles in a sunburst and areas in circle packing are read less accurately than positions, and distances in a t-SNE map are not distances in the data. Use them to reveal patterns; confirm the key numbers with a table.

Caveats up front. Every number here comes from synthetic data: it tests the method, not Thai tourism. And recovery is statistical. It shows the information is in the view, not that readers will see it. That is the next study.

Everything is open: the 19-page paper, code that rebuilds every number and figure with one command, the data on Hugging Face and a DOI. Links in the first comment.

If you work with tourism, mobility or card-payment data: which of these twelve would you show a decision-maker, and which real dataset should the framework meet first?

Personal research; views are my own.

#DataVisualization #TourismAnalytics #VisualAnalytics #OpenScience #Thailand

---

## First comment (links)

Read the paper: https://thanatchon36.github.io/twelve-views-thai-tourism/paper/
PDF: https://github.com/thanatchon36/twelve-views-thai-tourism/raw/main/paper/paper.pdf
Code: https://github.com/thanatchon36/twelve-views-thai-tourism
Data: https://huggingface.co/datasets/thanatchon36/twelve-views-thai-tourism
DOI: https://doi.org/10.5281/zenodo.24035604

---

## Post (Thai)

ข้อมูลท่องเที่ยวมีหลายรูปทรง แต่รายงานส่วนใหญ่ใช้กราฟอยู่แค่สองแบบ

จำนวนนักท่องเที่ยวรายเดือนคือวัฏจักร การเดินทางจากตลาดต้นทางไปยังจุดหมายคือ flow โครงสร้างการใช้จ่ายคือลำดับชั้น จังหวัดที่ถูกเที่ยวในทริปเดียวกันคือเครือข่าย และแบบสำรวจนักท่องเที่ยวคือกลุ่มของคนจำนวนมากที่แต่ละคนมีหลายมิติ พอบีบทั้งหมดลงในกราฟแท่งกับกราฟเส้น โครงสร้างที่เราอยากเห็นก็ต้องกลับไปขุดหาจากตารางเอง

working paper ชิ้นใหม่ของผมจึงตั้งคำถามสองข้อ
1. ภาพแบบไหนเหมาะกับคำถามด้านการท่องเที่ยวแบบไหน
2. ภาพแต่ละแบบแสดงโครงสร้างที่มันอ้างว่าแสดงได้จริงหรือไม่

4 คำถาม 12 views แต่ละภาพเลือกจากรูปทรงของข้อมูลที่คำถามนั้นต้องใช้
• ใครมาเที่ยว และมาเมื่อไร: unit chart, radial spiral, streamgraph, ridgeline plot
• นักท่องเที่ยวไปที่ไหน: Sankey diagram, chord diagram, hierarchical edge bundling
• เงินไปอยู่ที่ไหน: circle packing, sunburst, beeswarm
• นักท่องเที่ยวมีกี่แบบ: parallel coordinates, t-SNE embedding map

คำถามข้อสองยากกว่า เพราะกับข้อมูลจริงเราไม่มีทางรู้โครงสร้างที่แท้จริง จึงตรวจไม่ได้ว่ากราฟเผยมันออกมาหรือเปล่า ผมจึง "ฝัง" โครงสร้างลงไปเอง ในข้อมูลสังเคราะห์ 10 ชุด ปี 2010 ถึง 2025 ทั้งฤดูกาลที่รู้ค่าแน่นอน การดิ่งลงช่วงโรคระบาด ความชอบจุดหมายปลายทาง กรุงเทพฯ ในฐานะศูนย์กลางของการเดินทางต่อ รายได้ที่กระจุกตัว และ persona นักท่องเที่ยว 6 กลุ่มที่ซ่อนอยู่ แล้วให้ภาพแต่ละแบบมีค่าสถิติประกอบที่วัดว่าดึงโครงสร้างกลับมาได้แค่ไหน

ผลที่ได้
→ ฤดูกาล: r = 0.998 (radial spiral)
→ ค่ามัธยฐานของจำนวนคืนที่พัก: คลาดเฉลี่ย 0.32 คืน (ridgeline plot)
→ ความชอบจุดหมายปลายทาง: คลาดเฉลี่ย 0.37 percentage point (Sankey diagram)
→ persona ทั้ง 6 กลุ่ม: adjusted Rand index 0.85 (embedding map)
ความคลาดเคลื่อนที่เหลือทุกจุดอธิบายได้ด้วยที่มาที่รู้อยู่แล้ว คือ noise ที่ใส่ลงไป การปัดเศษ หรือการนับคืนเป็นจำนวนเต็ม

บทเรียนสองข้อ
• คำถามเดียวมักต้องดูหลายระดับ Sankey บอกว่าแต่ละตลาดไปไหน chord diagram บอกว่าจุดหมายไหนส่งคนต่อให้กัน edge bundling บอกว่าจังหวัดไหนถูกเที่ยวคู่กัน ไม่มีภาพไหนแทนกันได้
• ภาพที่สื่อได้มากต้องแลกกับความแม่นยำ คนอ่านมุมใน sunburst และพื้นที่ใน circle packing ได้แม่นน้อยกว่าตำแหน่ง และระยะใน t-SNE ไม่ใช่ระยะจริงในข้อมูล ใช้มันเพื่อให้เห็น pattern แล้วยืนยันตัวเลขสำคัญด้วยตาราง

ข้อควรระวัง: ตัวเลขทั้งหมดมาจากข้อมูลสังเคราะห์ เป็นการทดสอบวิธี ไม่ใช่ข้อค้นพบเรื่องการท่องเที่ยวไทย และการ recover นี้เป็นระดับสถิติ คือพิสูจน์ว่าข้อมูลอยู่ในภาพ ไม่ได้พิสูจน์ว่าผู้อ่านจะมองเห็น การทดสอบกับผู้อ่านจริงคือก้าวต่อไป

ทุกอย่างเปิดหมด: working paper 19 หน้า อ่านบนเว็บได้ด้วย โค้ดที่สร้างทุกตัวเลข ทุกตาราง และทุกภาพใหม่ได้ด้วยคำสั่งเดียว ข้อมูลบน Hugging Face และ DOI บน Zenodo ลิงก์อยู่ในคอมเมนต์แรกครับ

ใครทำงานกับข้อมูลท่องเที่ยว mobility หรือการใช้จ่ายผ่านบัตร ใน 12 ภาพนี้ ภาพไหนที่คุณจะเอาไปให้ผู้ตัดสินใจดู และกรอบนี้ควรไปเจอข้อมูลจริงชุดไหนก่อน?

งานวิจัยส่วนตัว ความเห็นเป็นของผมเอง

#DataVisualization #TourismAnalytics #VisualAnalytics #OpenScience #Thailand

---

## Short version (English)

Tourism data come in many shapes: cycles, flows, hierarchies, networks, profiles. Most reports use two charts.

I matched four tourism questions to twelve visual idioms, then planted known structure in synthetic data to test whether each view shows what it claims:
• seasonal profile recovered at r = 0.998 (radial spiral)
• median length of stay within 0.32 nights (ridgeline plot)
• six hidden traveller personas found again, ARI 0.85 (embedding map)

All data synthetic: a test of the method, not of Thai tourism. Paper, code, data and DOI in the first comment.

#DataVisualization #TourismAnalytics #OpenScience
