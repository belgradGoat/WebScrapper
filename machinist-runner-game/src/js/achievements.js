// Achievement system for Machinist Runner
class Achievement {
    constructor(id, name, description, icon, condition, points = 100) {
        this.id = id;
        this.name = name;
        this.description = description;
        this.icon = icon;
        this.condition = condition;
        this.points = points;
        this.unlocked = false;
        this.unlockedAt = null;
    }

    check(gameData) {
        if (this.unlocked) return false;
        
        if (this.condition(gameData)) {
            this.unlock();
            return true;
        }
        return false;
    }

    unlock() {
        this.unlocked = true;
        this.unlockedAt = Date.now();
        
        // Show achievement notification
        showAchievement(this);
        
        // Add particles effect
        if (typeof particleSystem !== 'undefined' && typeof player !== 'undefined') {
            particleSystem.addParticles(player.x, player.y, 20, '#FFD700', 'star');
            addScreenShake(4, 20);
        }
        
        // Play achievement sound
        if (typeof soundManager !== 'undefined') {
            soundManager.playComplete();
        }
    }
}

class AchievementManager {
    constructor() {
        this.achievements = [];
        this.initializeAchievements();
        this.totalPoints = 0;
        this.loadProgress();
    }

    initializeAchievements() {
        this.achievements = [
            new Achievement(
                'first_order',
                'Getting Started',
                'Complete your first work order',
                '🎯',
                (data) => data.totalOrdersCompleted >= 1,
                50
            ),
            new Achievement(
                'speed_demon',
                'Speed Demon',
                'Complete 5 orders in a single level',
                '⚡',
                (data) => data.completedOrdersThisLevel >= 5,
                150
            ),
            new Achievement(
                'survivor',
                'Survivor',
                'Reach level 5',
                '🏆',
                (data) => data.level >= 5,
                200
            ),
            new Achievement(
                'perfectionist',
                'Perfectionist',
                'Complete 10 consecutive orders without failing QC',
                '✨',
                (data) => data.consecutiveQCPasses >= 10,
                300
            ),
            new Achievement(
                'efficiency_expert',
                'Efficiency Expert',
                'Score 5000 points',
                '💎',
                (data) => data.score >= 5000,
                250
            ),
            new Achievement(
                'marathon_runner',
                'Marathon Runner',
                'Play for 10 minutes straight',
                '🏃',
                (data) => (Date.now() - data.gameStartTime) >= 600000,
                200
            ),
            new Achievement(
                'dodger',
                'Master Dodger',
                'Avoid enemies for 2 minutes straight',
                '🥷',
                (data) => data.timeSinceLastCollision >= 120000,
                300
            ),
            new Achievement(
                'multitasker',
                'Multitasker',
                'Have 3 active work orders at once',
                '🎪',
                (data) => data.activeOrders >= 3,
                150
            )
        ];
    }

    checkAchievements(gameData) {
        this.achievements.forEach(achievement => {
            if (achievement.check(gameData)) {
                this.totalPoints += achievement.points;
                this.saveProgress();
            }
        });
    }

    getUnlockedAchievements() {
        return this.achievements.filter(a => a.unlocked);
    }

    getProgress() {
        const total = this.achievements.length;
        const unlocked = this.getUnlockedAchievements().length;
        return { unlocked, total, percentage: Math.round((unlocked / total) * 100) };
    }

    saveProgress() {
        const data = {
            achievements: this.achievements.map(a => ({
                id: a.id,
                unlocked: a.unlocked,
                unlockedAt: a.unlockedAt
            })),
            totalPoints: this.totalPoints
        };
        localStorage.setItem('machinistRunnerAchievements', JSON.stringify(data));
    }

    loadProgress() {
        try {
            const data = JSON.parse(localStorage.getItem('machinistRunnerAchievements') || '{}');
            if (data.achievements) {
                data.achievements.forEach(saved => {
                    const achievement = this.achievements.find(a => a.id === saved.id);
                    if (achievement) {
                        achievement.unlocked = saved.unlocked;
                        achievement.unlockedAt = saved.unlockedAt;
                    }
                });
            }
            this.totalPoints = data.totalPoints || 0;
        } catch (error) {
            console.log('Could not load achievement progress');
        }
    }
}

function showAchievement(achievement) {
    // Create achievement notification
    const notification = document.createElement('div');
    notification.className = 'achievement-notification';
    notification.innerHTML = `
        <div class="achievement-icon">${achievement.icon}</div>
        <div class="achievement-content">
            <div class="achievement-title">Achievement Unlocked!</div>
            <div class="achievement-name">${achievement.name}</div>
            <div class="achievement-description">${achievement.description}</div>
            <div class="achievement-points">+${achievement.points} points</div>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Animate in
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Remove after delay
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => document.body.removeChild(notification), 500);
    }, 4000);
}

// Global achievement manager
const achievementManager = new AchievementManager();

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Achievement, AchievementManager };
}
