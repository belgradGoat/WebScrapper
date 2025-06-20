const EVE_REGION_LAYOUT = {
    // Empire Space - Center Ring
    "The Forge": { x: 0, y: 0, group: "highsec", color: "#00ff00" },
    "Domain": { x: -2, y: 0, group: "highsec", color: "#00ff00" },
    "Sinq Laison": { x: -1, y: -1, group: "highsec", color: "#00ff00" },
    "Heimatar": { x: 1, y: -1, group: "highsec", color: "#00ff00" },
    "Metropolis": { x: 2, y: 0, group: "highsec", color: "#00ff00" },
    "The Citadel": { x: 0, y: -1, group: "highsec", color: "#00ff00" },
    "Essence": { x: -2, y: -1, group: "highsec", color: "#00ff00" },
    "Tash-Murkon": { x: 1, y: 1, group: "highsec", color: "#00ff00" },
    "Everyshore": { x: -1, y: 1, group: "highsec", color: "#00ff00" },
    "Kador": { x: 0, y: 1, group: "highsec", color: "#00ff00" },
    
    // Low-Sec Buffer
    "Lonetrek": { x: 1, y: -2, group: "lowsec", color: "#ffff00" },
    "Black Rise": { x: 2, y: -2, group: "lowsec", color: "#ffff00" },
    "Placid": { x: -2, y: -2, group: "lowsec", color: "#ffff00" },
    "Verge Vendor": { x: -3, y: -1, group: "lowsec", color: "#ffff00" },
    "Molden Heath": { x: 3, y: -1, group: "lowsec", color: "#ffff00" },
    "Genesis": { x: -3, y: 1, group: "lowsec", color: "#ffff00" },
    "Aridia": { x: -2, y: 2, group: "lowsec", color: "#ffff00" },
    "Derelik": { x: 2, y: 2, group: "lowsec", color: "#ffff00" },
    "Devoid": { x: 0, y: 2, group: "lowsec", color: "#ffff00" },
    "The Bleak Lands": { x: 1, y: 2, group: "lowsec", color: "#ffff00" },
    
    // Null-Sec North
    "Deklein": { x: -1, y: -4, group: "nullsec", color: "#ff4444" },
    "Pure Blind": { x: -2, y: -3, group: "nullsec", color: "#ff4444" },
    "Tribute": { x: 1, y: -3, group: "nullsec", color: "#ff4444" },
    "Vale of the Silent": { x: 2, y: -3, group: "nullsec", color: "#ff4444" },
    "Geminate": { x: 3, y: -2, group: "nullsec", color: "#ff4444" },
    "Tenal": { x: 0, y: -4, group: "nullsec", color: "#ff4444" },
    "Branch": { x: -3, y: -3, group: "nullsec", color: "#ff4444" },
    "Venal": { x: 0, y: -3, group: "nullsec", color: "#ff4444" },
    
    // Null-Sec East
    "Cache": { x: 4, y: -1, group: "nullsec", color: "#ff4444" },
    "Insmother": { x: 4, y: 0, group: "nullsec", color: "#ff4444" },
    "Detorid": { x: 4, y: 1, group: "nullsec", color: "#ff4444" },
    "Scalding Pass": { x: 4, y: 2, group: "nullsec", color: "#ff4444" },
    "Wicked Creek": { x: 5, y: 1, group: "nullsec", color: "#ff4444" },
    "Great Wildlands": { x: 3, y: 0, group: "nullsec", color: "#ff4444" },
    "Curse": { x: 3, y: 1, group: "nullsec", color: "#ff4444" },
    
    // Null-Sec South
    "Providence": { x: 3, y: 3, group: "nullsec", color: "#ff4444" },
    "Catch": { x: 2, y: 3, group: "nullsec", color: "#ff4444" },
    "Impass": { x: 1, y: 4, group: "nullsec", color: "#ff4444" },
    "Feythabolis": { x: 0, y: 4, group: "nullsec", color: "#ff4444" },
    "Omist": { x: -1, y: 4, group: "nullsec", color: "#ff4444" },
    "Tenerifis": { x: -2, y: 4, group: "nullsec", color: "#ff4444" },
    "Immensea": { x: 1, y: 3, group: "nullsec", color: "#ff4444" },
    "Paragon Soul": { x: -3, y: 4, group: "nullsec", color: "#ff4444" },
    "Esoteria": { x: -4, y: 4, group: "nullsec", color: "#ff4444" },
    
    // Null-Sec West
    "Delve": { x: -3, y: 3, group: "nullsec", color: "#ff4444" },
    "Period Basis": { x: -4, y: 3, group: "nullsec", color: "#ff4444" },
    "Querious": { x: -4, y: 2, group: "nullsec", color: "#ff4444" },
    "Fountain": { x: -4, y: 0, group: "nullsec", color: "#ff4444" },
    "Cloud Ring": { x: -3, y: -2, group: "nullsec", color: "#ff4444" },
    "Fade": { x: -4, y: -3, group: "nullsec", color: "#ff4444" },
    "Outer Ring": { x: -5, y: 0, group: "nullsec", color: "#ff4444" },
    "Syndicate": { x: -4, y: -1, group: "nullsec", color: "#ff4444" },
    "Solitude": { x: -5, y: -2, group: "nullsec", color: "#ff4444" }
};

// Define region connections for cleaner visualization
const REGION_CONNECTIONS = [
    // High-sec core connections
    ["The Forge", "The Citadel"],
    ["The Forge", "Lonetrek"],
    ["The Forge", "Sinq Laison"],
    ["Domain", "Genesis"],
    ["Domain", "Tash-Murkon"],
    ["Domain", "Kador"],
    ["Heimatar", "Metropolis"],
    ["Heimatar", "Molden Heath"],
    
    // Low-sec to null-sec connections
    ["Lonetrek", "Pure Blind"],
    ["Black Rise", "Tribute"],
    ["Placid", "Syndicate"],
    ["Genesis", "Fountain"],
    ["Aridia", "Delve"],
    ["Derelik", "Curse"],
    
    // Major null-sec highways
    ["Pure Blind", "Deklein"],
    ["Tribute", "Vale of the Silent"],
    ["Delve", "Period Basis"],
    ["Providence", "Catch"],
    ["Catch", "Impass"],
    ["Fountain", "Cloud Ring"],
    ["Cloud Ring", "Fade"]
];

// Export for use in main app
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { EVE_REGION_LAYOUT, REGION_CONNECTIONS };
}