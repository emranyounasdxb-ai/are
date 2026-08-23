# ALIYAS Real Estate Website

This repository contains the official website redesign project for **ALIYAS Real Estate**.

The goal is to create a modern, premium and user-friendly real estate website that presents the company, properties and services professionally while making it easy for customers to explore opportunities and submit enquiries.

## Project Overview

The website is being redesigned to provide a stronger digital presence for ALIYAS Real Estate in the UAE property market.

The new website will focus on:

* Modern and premium visual design
* Clear property presentation
* Simple and user-friendly navigation
* Mobile, tablet and desktop responsiveness
* Fast and accessible browsing experience
* Clear contact and enquiry options
* Search-engine-friendly page structure
* Easy future expansion and maintenance

## Planned Website Sections

The website may include:

* Home
* About Us
* Property Listings
* Property Details
* Communities and Locations
* Real Estate Services
* Featured Projects
* Contact Us
* Property Enquiry Forms
* Privacy Policy and Legal Pages

Final pages and content will be confirmed during the redesign process.

## Property Features

The redesigned platform is intended to support:

* Property cards with images and key information
* Property detail pages
* Location and community information
* Property type, price and location filters
* Featured and newly added properties
* Customer enquiry forms
* WhatsApp and direct-call options
* Agent or company contact information
* Related property recommendations

## Design Direction

The website should have a:

* Premium UAE real estate appearance
* Clean and modern interface
* Strong visual hierarchy
* Professional typography
* Consistent brand colour system
* High-quality property imagery
* Spacious and uncluttered layouts
* Smooth but controlled animations
* Clear calls to action
* Fully responsive mobile experience

The design must feel professional and trustworthy without looking like a generic real estate template.

## User Experience Goals

Visitors should be able to:

1. Understand the company and its services quickly.
2. Browse available properties easily.
3. View complete property information.
4. Find suitable contact and enquiry options.
5. Use the website comfortably on any screen size.
6. Move between pages without confusion or unnecessary steps.

## Development Principles

* Use reusable and maintainable components.
* Keep the interface consistent across all pages.
* Follow responsive design best practices.
* Optimise images and page performance.
* Apply basic accessibility standards.
* Avoid unnecessary dependencies and animations.
* Keep sensitive information out of the repository.
* Do not publish unapproved content or contact details.

## Content Governance

All company information, property details, contact information, legal content and marketing claims must be reviewed and approved before production release.

Placeholder or sample content must be clearly identified and must not be presented as final information.

## Project Status

**Status:** Website redesign in progress.

Development, design, content preparation and testing will be completed in controlled stages before the production launch.

## Brand

**Company:** ALIYAS Real Estate
**Market:** United Arab Emirates
**Project Type:** Official real estate website redesign
**Repository Purpose:** Website design, development and maintenance

## License

This project and its contents are intended for ALIYAS Real Estate. All brand assets, content, designs and source code are subject to the company’s ownership and usage policies.

## Local Frontend Development

The current frontend is a development-only technical scaffold. It does not contain the real homepage, Admin Dashboard, authentication, business data, or final ARE design system.

### Prerequisites

* Node.js `24.18.0`
* npm `11.16.0`

### Install dependencies

Run `npm ci` from the repository root. The repository uses npm workspaces and one root `package-lock.json`.

### Run the public application

Run `npm run dev:public`, then use `http://127.0.0.1:50001`.

### Run the Admin application

Run `npm run dev:admin`, then use `http://127.0.0.1:50002`.

### Validate the workspace

* `npm run lint`
* `npm run typecheck`
* `npm run build`

Port `3000` belongs to another protected local project. ARE commands must never bind, stop, restart, or otherwise interfere with port `3000`.

## Local Mobile Development

Run `npm run dev:mobile` from the repository root to start Expo Metro in development-build mode on `127.0.0.1:50018`. The command checks that the reserved port is free and does not launch a browser, emulator, or simulator.

Android development requires an installed Expo development build. Windows supports the local Android toolchain; local iOS Simulator builds require macOS and Xcode. This scaffold has no browser-based mobile target. Physical-device networking and iPhone development remain separate owner-approved tasks.
