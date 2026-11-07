"""Category labels used throughout the pipeline.

Keeping every label in one module keeps the analysis and plotting code free
of hard-coded strings; relabelling the figures is a one-file change.
"""

# Source markets grouped into six origin regions (index = region_id)
ORIGIN_REGIONS = ["East Asia", "ASEAN", "Europe", "South Asia", "Americas", "Oceania & other"]

# Six-region geography of Thailand (index = thai_region_id)
THAI_REGIONS = ["North", "Northeast", "Central", "East", "West", "South"]

# Destination clusters used for trip flows (index = dest_id)
DEST_CLUSTERS = ["Bangkok", "Phuket & Andaman", "Samui & Gulf", "Pattaya & East",
                 "Chiang Mai & North", "Border towns & other"]

# Main purpose of the trip (index = style_id)
TRIP_STYLES = ["Beach & islands", "City & shopping", "Culture & nature", "Business & MICE"]

# Latent traveller personas behind the synthetic survey (index = segment_id)
PERSONAS = ["Long-stay beach", "City shoppers", "Culture seekers", "Backpackers",
            "Business travellers", "Family holidaymakers"]

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTHS_FULL = ["January", "February", "March", "April", "May", "June", "July", "August",
               "September", "October", "November", "December"]

# All 77 provinces by Thai region (keys match THAI_REGIONS)
PROVINCES = {
    0: ["Chiang Mai", "Chiang Rai", "Lampang", "Lamphun", "Mae Hong Son", "Nan", "Phayao", "Phrae",
        "Uttaradit"],
    1: ["Kalasin", "Khon Kaen", "Chaiyaphum", "Nakhon Phanom", "Nakhon Ratchasima", "Bueng Kan",
        "Buriram", "Maha Sarakham", "Mukdahan", "Yasothon", "Roi Et", "Loei", "Sisaket", "Sakon Nakhon",
        "Surin", "Nong Khai", "Nong Bua Lamphu", "Amnat Charoen", "Udon Thani", "Ubon Ratchathani"],
    2: ["Bangkok", "Kamphaeng Phet", "Chai Nat", "Nakhon Nayok", "Nakhon Pathom", "Nakhon Sawan",
        "Nonthaburi", "Pathum Thani", "Phra Nakhon Si Ayutthaya", "Phichit", "Phitsanulok", "Phetchabun",
        "Lopburi", "Samut Prakan", "Samut Songkhram", "Samut Sakhon", "Sing Buri", "Sukhothai",
        "Suphan Buri", "Saraburi", "Ang Thong", "Uthai Thani"],
    3: ["Chanthaburi", "Chachoengsao", "Chonburi", "Trat", "Prachinburi", "Rayong", "Sa Kaeo"],
    4: ["Kanchanaburi", "Tak", "Prachuap Khiri Khan", "Phetchaburi", "Ratchaburi"],
    5: ["Krabi", "Chumphon", "Trang", "Nakhon Si Thammarat", "Narathiwat", "Pattani", "Phang Nga",
        "Phatthalung", "Phuket", "Ranong", "Satun", "Songkhla", "Surat Thani", "Yala"],
}

# Short display names for long province names in tight labels
SHORT_NAMES = {
    "Phra Nakhon Si Ayutthaya": "Ayutthaya",
    "Prachuap Khiri Khan": "Prachuap",
    "Nakhon Ratchasima": "Korat",
    "Ubon Ratchathani": "Ubon",
    "Nakhon Si Thammarat": "Nakhon Si Th.",
}
