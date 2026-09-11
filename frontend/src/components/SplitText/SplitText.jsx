import { useRef, useEffect, useState, useMemo } from 'react';
import { gsap } from 'gsap';
import { ScrollTrigger } from 'gsap/ScrollTrigger';
import { useGSAP } from '@gsap/react';

gsap.registerPlugin(ScrollTrigger);

const SplitText = ({
  text = '',
  className = '',
  delay = 50,
  duration = 1.25,
  ease = 'power3.out',
  splitType = 'chars',
  from = { opacity: 0, y: 40 },
  to = { opacity: 1, y: 0 },
  threshold = 0.1,
  rootMargin = '-100px',
  textAlign = 'left',
  tag = 'p',
  onLetterAnimationComplete
}) => {
  const ref = useRef(null);
  const animationCompletedRef = useRef(false);
  const onCompleteRef = useRef(onLetterAnimationComplete);

  useEffect(() => {
    onCompleteRef.current = onLetterAnimationComplete;
  }, [onLetterAnimationComplete]);

  // Split text into structure
  const words = useMemo(() => {
    if (!text) return [];
    return text.split(' ').map(word => ({
      word,
      chars: word.split('')
    }));
  }, [text]);

  useGSAP(
    () => {
      if (!ref.current || !text) return;
      if (animationCompletedRef.current) return;

      const el = ref.current;
      let targets;

      if (splitType.includes('chars')) {
        targets = el.querySelectorAll('.split-char');
      } else if (splitType.includes('words')) {
        targets = el.querySelectorAll('.split-word');
      } else {
        targets = [el];
      }

      if (!targets || targets.length === 0) return;

      const startPct = (1 - threshold) * 100;
      const marginMatch = /^(-?\d+(?:\.\d+)?)(px|em|rem|%)?$/.exec(rootMargin);
      const marginValue = marginMatch ? parseFloat(marginMatch[1]) : 0;
      const marginUnit = marginMatch ? marginMatch[2] || 'px' : 'px';
      const sign =
        marginValue === 0
          ? ''
          : marginValue < 0
            ? `-=${Math.abs(marginValue)}${marginUnit}`
            : `+=${marginValue}${marginUnit}`;
      const start = `top ${startPct}%${sign}`;

      const tween = gsap.fromTo(
        targets,
        { ...from },
        {
          ...to,
          duration,
          ease,
          stagger: delay / 1000,
          scrollTrigger: {
            trigger: el,
            start,
            once: true,
            fastScrollEnd: true,
            anticipatePin: 0.4
          },
          onComplete: () => {
            animationCompletedRef.current = true;
            onCompleteRef.current?.();
          },
          willChange: 'transform, opacity',
          force3D: true
        }
      );

      return () => {
        tween.kill();
        ScrollTrigger.getAll().forEach(st => {
          if (st.trigger === el) st.kill();
        });
      };
    },
    {
      dependencies: [
        text,
        delay,
        duration,
        ease,
        splitType,
        JSON.stringify(from),
        JSON.stringify(to),
        threshold,
        rootMargin
      ],
      scope: ref
    }
  );

  const Tag = tag || 'p';

  const containerStyle = {
    textAlign,
    display: 'inline-block',
    whiteSpace: 'normal',
    wordWrap: 'break-word',
    willChange: 'transform, opacity'
  };

  return (
    <Tag ref={ref} style={containerStyle} className={`split-parent ${className}`}>
      {words.map((wObj, wIndex) => (
        <span 
          key={wIndex} 
          className="split-word" 
          style={{ display: 'inline-block', whiteSpace: 'nowrap' }}
        >
          {splitType.includes('chars')
            ? wObj.chars.map((char, cIndex) => (
                <span
                  key={cIndex}
                  className="split-char"
                  style={{ display: 'inline-block', willChange: 'transform, opacity' }}
                >
                  {char}
                </span>
              ))
            : wObj.word}
          {wIndex < words.length - 1 && <span style={{ display: 'inline-block' }}>&nbsp;</span>}
        </span>
      ))}
    </Tag>
  );
};

export default SplitText;
