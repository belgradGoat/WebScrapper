// Particle system for visual effects
class Particle {
    constructor(x, y, color, type = 'spark') {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 4;
        this.vy = (Math.random() - 0.5) * 4 - 2;
        this.color = color;
        this.life = 1.0;
        this.decay = Math.random() * 0.02 + 0.02;
        this.size = Math.random() * 3 + 2;
        this.type = type;
        this.gravity = type === 'spark' ? 0.1 : 0.05;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        this.vy += this.gravity;
        this.life -= this.decay;
        
        if (this.type === 'spark') {
            this.vx *= 0.98;
            this.vy *= 0.98;
        }
        
        return this.life > 0;
    }

    draw(ctx) {
        if (this.life <= 0) return;
        
        ctx.save();
        ctx.globalAlpha = this.life;
        
        if (this.type === 'spark') {
            ctx.fillStyle = this.color;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size * this.life, 0, Math.PI * 2);
            ctx.fill();
        } else if (this.type === 'star') {
            this.drawStar(ctx);
        }
        
        ctx.restore();
    }

    drawStar(ctx) {
        const spikes = 5;
        const outerRadius = this.size * this.life;
        const innerRadius = outerRadius * 0.5;
        
        ctx.fillStyle = this.color;
        ctx.beginPath();
        ctx.translate(this.x, this.y);
        
        for (let i = 0; i < spikes * 2; i++) {
            const radius = i % 2 === 0 ? outerRadius : innerRadius;
            const angle = (i * Math.PI) / spikes;
            const x = Math.cos(angle) * radius;
            const y = Math.sin(angle) * radius;
            
            if (i === 0) {
                ctx.moveTo(x, y);
            } else {
                ctx.lineTo(x, y);
            }
        }
        
        ctx.closePath();
        ctx.fill();
        ctx.translate(-this.x, -this.y);
    }
}

class ParticleSystem {
    constructor() {
        this.particles = [];
    }

    addParticles(x, y, count, color, type = 'spark') {
        for (let i = 0; i < count; i++) {
            this.particles.push(new Particle(x, y, color, type));
        }
    }

    // Special effects for different events
    workOrderComplete(x, y) {
        this.addParticles(x, y, 15, '#00ff00', 'star');
        this.addParticles(x, y, 10, '#ffff00', 'spark');
    }

    stationActivated(x, y, stationType) {
        const colors = {
            'cad': '#00ffff',
            'material': '#ff8800',
            'machine': '#888888',
            'qc': '#0088ff',
            'shipping': '#00ff88'
        };
        
        const color = colors[stationType] || '#ffffff';
        this.addParticles(x, y, 8, color, 'spark');
    }

    playerCaught(x, y) {
        this.addParticles(x, y, 20, '#ff0000', 'spark');
        this.addParticles(x, y, 5, '#ffaa00', 'star');
    }

    levelUp(x, y) {
        this.addParticles(x, y, 25, '#ff00ff', 'star');
        this.addParticles(x, y, 15, '#ffff00', 'spark');
    }

    update() {
        this.particles = this.particles.filter(particle => particle.update());
    }

    draw(ctx) {
        this.particles.forEach(particle => particle.draw(ctx));
    }

    clear() {
        this.particles = [];
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { Particle, ParticleSystem };
}
