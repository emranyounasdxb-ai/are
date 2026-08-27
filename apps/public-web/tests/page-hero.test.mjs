import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';
import test from 'node:test';
import vm from 'node:vm';
import React from 'react';
import { renderToStaticMarkup } from 'react-dom/server';
import ts from 'typescript';

const require = createRequire(import.meta.url);
const source = name => readFileSync(new URL(`../components/hero/${name}`, import.meta.url), 'utf8');
function compile(name, imports = {}) {
  const output = ts.transpileModule(source(name), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX, esModuleInterop: true },
  }).outputText;
  const exports = {};
  vm.runInNewContext(output, { exports, require: id => id in imports ? imports[id] : require(id) });
  return exports;
}
const { heroImages } = compile('hero-images.ts');
const { PageHero } = compile('page-hero.tsx', {
  'next/image': ({ fill, preload, ...props }) => React.createElement('img', { ...props, 'data-fill': String(fill), 'data-preload': String(preload) }),
  'next/link': props => React.createElement('a', props),
  '../motion/reveal': { Reveal: ({ distance, ...props }) => React.createElement('div', { ...props, 'data-distance': distance }) },
  '../motion/home-hero-shiny-eyebrow': { HomeHeroShinyEyebrow: ({ text }) => React.createElement('span', { 'data-shiny': true }, text) },
  '../motion/home-hero-typed-description': { HomeHeroTypedDescription: ({ text, locale }) => React.createElement('span', { dir: locale === 'ar' ? 'rtl' : 'ltr', 'data-description': true }, text) },
  './hero-images': { heroImages },
  './page-hero.module.css': { __esModule: true, default: new Proxy({}, { get: (_, key) => String(key) }) },
});

test('each requested hero uses a distinct existing readable approved editorial image', async () => {
  assert.deepEqual(Object.keys(heroImages), ['buy', 'rent', 'off-plan', 'developers', 'communities', 'insights', 'careers', 'contact']);
  assert.equal(new Set(Object.values(heroImages).map(asset => asset.file)).size, 8);
  const sharp = require('sharp');
  for (const asset of Object.values(heroImages)) {
    const bytes = readFileSync(new URL(`../public/images/home-premium/${asset.file}`, import.meta.url));
    const metadata = await sharp(bytes).metadata();
    assert.equal(metadata.format, 'webp');
    assert.ok(metadata.width >= 1400 && metadata.height >= 800);
    await sharp(bytes).resize(16, 16).raw().toBuffer();
    assert.ok(asset.en && /[\u0600-\u06ff]/.test(asset.ar));
    for (const key of ['desktop', 'mobile', 'rtl', 'rtlMobile']) assert.match(asset[key], /^\d+% \d+%$/);
  }
});

test('all EN/AR variants retain one semantic heading, localized alt and real links', () => {
  for (const locale of ['en', 'ar']) for (const image of Object.keys(heroImages)) {
    const html = renderToStaticMarkup(React.createElement(PageHero, {
      locale, image, title: 'A title', eyebrow: 'An eyebrow', description: 'Complete description',
      primary: { label: 'Explore', href: '#directory' }, secondary: { label: 'Contact', href: `/${locale}/contact` },
    }));
    assert.equal((html.match(/<h1\b/g) ?? []).length, 1);
    assert.match(html, /aria-labelledby="page-hero-title"/);
    assert.ok(html.includes(`alt="${heroImages[image][locale]}"`));
    assert.match(html, /data-fill="true" data-preload="true"/);
    assert.match(html, /sizes="100vw"/);
    assert.match(html, /href="#directory"/);
    assert.ok(html.includes(`href="/${locale}/contact"`));
    assert.equal((html.match(/animated-gold-border/g) ?? []).length, 1);
    assert.equal(html.includes('data-shiny="true"'), locale === 'en');
    assert.ok(html.includes(`dir="${locale === 'ar' ? 'rtl' : 'ltr'}"`));
    assert.match(html, /data-distance="18"/);
  }
});

test('optional secondary action and informational note do not create empty controls', () => {
  const html = renderToStaticMarkup(React.createElement(PageHero, {
    locale: 'en', image: 'contact', title: 'Contact', eyebrow: 'Contact', description: 'Description',
    primary: { label: 'Enquire', href: '#contact-form-title' },
  }));
  assert.equal((html.match(/<a\b/g) ?? []).length, 1);
  assert.ok(!html.includes('<aside'));
});

test('shared styling preserves master scale, natural RTL and mobile flow without mirroring', () => {
  const css = source('page-hero.module.css');
  assert.match(css, /min-height: min\(55rem, 94svh\)/);
  assert.match(css, /clamp\(4\.5rem, 6vw, 5\.4rem\)/);
  assert.match(css, /object-fit: cover/);
  assert.match(css, /:dir\(rtl\)/);
  assert.match(css, /@media \(max-width: 700px\)/);
  assert.ok(!/scaleX|rotateY|font-family/.test(css));
  assert.ok(!source('page-hero.tsx').includes('use client'));
});

test('existing motion components retain reduced-motion and static accessible description safeguards', () => {
  const motionSource = name => readFileSync(new URL(`../components/motion/${name}`, import.meta.url), 'utf8');
  assert.match(motionSource('reveal.tsx'), /useReducedMotion/);
  assert.match(motionSource('home-hero-shiny-eyebrow.tsx'), /useReducedMotion/);
  const description = motionSource('home-hero-typed-description.tsx');
  assert.match(description, /prefers-reduced-motion: reduce/);
  assert.match(description, /playedDescriptions\.has/);
  assert.match(description, /className="visually-hidden">\{text\}/);
  assert.match(description, /loop=\{false\}/);
  assert.match(description, /typingSpeed=\{55\}/);
});

test('reused reveal and eyebrow render statically when reduced motion is requested', () => {
  let revealProps;
  const { Reveal } = compile('../motion/reveal.tsx', {
    'motion/react': { useReducedMotion: () => true },
    'motion/react-m': { div: props => { revealProps = props; return React.createElement('div', null, props.children); } },
    './tokens': { cinematicEase: [0.22, 1, 0.36, 1], motionDuration: { hero: 0.82 } },
  });
  renderToStaticMarkup(React.createElement(Reveal, { distance: 18 }, 'Visible content'));
  assert.equal(revealProps.initial.opacity, 1);
  assert.equal(revealProps.initial.y, undefined);
  assert.equal(revealProps.transition.duration, 0);
  const { HomeHeroShinyEyebrow } = compile('../motion/home-hero-shiny-eyebrow.tsx', {
    'motion/react': { useReducedMotion: () => true },
    '../ShinyText': () => { throw new Error('Reduced motion must not mount ShinyText'); },
  });
  assert.equal(renderToStaticMarkup(React.createElement(HomeHeroShinyEyebrow, { text: 'Static eyebrow' })), '<span>Static eyebrow</span>');
});
