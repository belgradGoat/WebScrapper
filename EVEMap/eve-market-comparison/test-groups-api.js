/**
 * Test script to explore EVE Online Groups API
 * Tests the /universe/groups/{group_id}/ endpoint
 */

async function testGroupsAPI() {
    console.log('🔍 Testing EVE Groups API');
    console.log('========================');
    
    // Test some common group IDs to understand the data structure
    const testGroupIds = [
        25,  // Frigate
        26,  // Cruiser  
        27,  // Battleship
        7,   // Module - Armor
        8,   // Module - Electronics
        87,  // Projectile Ammunition
        18,  // Mineral
        4    // Material
    ];
    
    for (const groupId of testGroupIds) {
        try {
            console.log(`\n📡 Testing group ID: ${groupId}`);
            
            const response = await fetch(`https://esi.evetech.net/latest/universe/groups/${groupId}/`);
            
            if (response.ok) {
                const groupData = await response.json();
                console.log(`✅ Group ${groupId}:`, {
                    name: groupData.name,
                    category_id: groupData.category_id,
                    published: groupData.published,
                    types_count: groupData.types ? groupData.types.length : 0
                });
                
                if (groupData.types && groupData.types.length > 0) {
                    console.log(`   📦 Sample types: ${groupData.types.slice(0, 3).join(', ')}...`);
                }
            } else {
                console.log(`❌ Group ${groupId}: HTTP ${response.status}`);
            }
            
            // Small delay to be nice to the API
            await new Promise(resolve => setTimeout(resolve, 100));
            
        } catch (error) {
            console.error(`❌ Error testing group ${groupId}:`, error.message);
        }
    }
    
    // Test getting all groups
    console.log('\n📡 Testing all groups endpoint...');
    try {
        const response = await fetch('https://esi.evetech.net/latest/universe/groups/');
        if (response.ok) {
            const allGroups = await response.json();
            console.log(`✅ Total groups available: ${allGroups.length}`);
            console.log(`   Sample group IDs: ${allGroups.slice(0, 10).join(', ')}...`);
        } else {
            console.log(`❌ All groups: HTTP ${response.status}`);
        }
    } catch (error) {
        console.error('❌ Error getting all groups:', error.message);
    }
}

// Run the test
testGroupsAPI();
