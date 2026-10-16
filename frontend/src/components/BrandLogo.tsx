/**
 * Official ProcuraX Brand Logo Component
 * Matches the user-provided blueprint with the 3D glowing neon emblem,
 * bold high-tech wordmark, and AI-native decision intelligence tagline.
 */
interface BrandLogoProps {
  size?: 'sm' | 'md' | 'lg'
  variant?: 'light' | 'dark'
  showTagline?: boolean
  tagline?: string
  companyName?: string
  onClick?: () => void
}

export function BrandLogo({
  size = 'md',
  variant = 'light',
  showTagline = true,
  tagline = 'AI-Native Decision Intelligence',
  companyName,
  onClick,
}: BrandLogoProps) {
  const isLg = size === 'lg'
  const isSm = size === 'sm'

  return (
    <div
      className={`procurax-brand-logo ${variant} ${size}`}
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: isSm ? '9px' : isLg ? '14px' : '11px',
        cursor: onClick ? 'pointer' : 'default',
        textDecoration: 'none',
        userSelect: 'none',
      }}
    >
      {/* 3D Glowing Neon Emblem */}
      <div
        className="brand-emblem-wrap"
        style={{
          position: 'relative',
          width: isSm ? '30px' : isLg ? '46px' : '38px',
          height: isSm ? '30px' : isLg ? '46px' : '38px',
          borderRadius: isSm ? '8px' : '11px',
          overflow: 'hidden',
          boxShadow: '0 0 16px rgba(14, 165, 233, 0.45), 0 0 4px rgba(0, 242, 254, 0.6)',
          border: '1px solid rgba(56, 189, 248, 0.3)',
          background: '#090d16',
          flexShrink: 0,
          display: 'grid',
          placeItems: 'center',
          transition: 'transform 0.25s ease, box-shadow 0.25s ease',
        }}
      >
        <img
          src="/procurax-neon-emblem.webp"
          alt="ProcuraX Official Emblem"
          style={{
            width: '100%',
            height: '100%',
            objectFit: 'cover',
            display: 'block',
          }}
        />
      </div>

      {/* Wordmark & Tagline */}
      <div style={{ display: 'flex', flexDirection: 'column', lineHeight: 1 }}>
        <div
          style={{
            fontFamily: "'Manrope', sans-serif",
            fontWeight: 800,
            fontSize: isSm ? '15px' : isLg ? '22px' : '18px',
            letterSpacing: '-0.5px',
            color: variant === 'dark' ? '#0f172a' : '#ffffff',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            flexWrap: 'nowrap',
          }}
        >
          <span>
            Procura
            <span
              style={{
                background: 'linear-gradient(135deg, #00f2fe 0%, #38bdf8 50%, #818cf8 100%)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent',
                marginLeft: '1px',
                textShadow: '0 0 12px rgba(56, 189, 248, 0.4)',
              }}
            >
              X
            </span>
          </span>
          {companyName && (
            <span
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '5px',
                fontSize: isSm ? '11px' : isLg ? '15px' : '13px',
                fontWeight: 700,
                color: variant === 'dark' ? '#E58B45' : '#176B55',
              }}
            >
              <span style={{ color: variant === 'dark' ? '#64716B' : '#94a3b8', fontWeight: 400 }}>×</span>
              <span>{companyName}</span>
            </span>
          )}
        </div>
        {showTagline && (
          <small
            style={{
              fontFamily: "'DM Mono', monospace",
              fontSize: isSm ? '7px' : isLg ? '9px' : '8px',
              fontWeight: 600,
              letterSpacing: '0.8px',
              textTransform: 'uppercase',
              color: variant === 'dark' ? '#64748b' : '#94a3b8',
              marginTop: '4px',
            }}
          >
            {tagline}
          </small>
        )}
      </div>
    </div>
  )
}
