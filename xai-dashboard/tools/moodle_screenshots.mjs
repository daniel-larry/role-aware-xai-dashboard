// Log in to the real Moodle as each staff role and capture the local_xairisk pages.
// Usage: npm i playwright && STAFF_PASSWORD=... OUT=docs/screenshots/moodle node tools/moodle_screenshots.mjs
import { chromium } from 'playwright'

const BASE = process.env.MOODLE || 'http://localhost:8080'
const OUT = process.env.OUT || '.'
const PASS = process.env.STAFF_PASSWORD
const browser = await chromium.launch({ ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) })

async function skipTour(page) {
  const b = page.locator('button:has-text("Skip tour"), button:has-text("End tour")').first()
  if (await b.isVisible().catch(() => false)) await b.click()
}

async function session(user) {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 1000 } })
  const page = await ctx.newPage()
  await page.goto(`${BASE}/login/index.php`)
  await page.fill('#username', user)
  await page.fill('#password', PASS)
  await page.click('#loginbtn')
  await page.waitForLoadState('networkidle')
  await skipTour(page)
  if (page.url().includes('/login/')) throw new Error(`login failed for ${user}`)
  return { ctx, page }
}

// Instructor: open course FFF-2014J, follow the course navigation link, explain one student.
{
  const { ctx, page } = await session('instructor_fff')
  await page.goto(`${BASE}/course/search.php?search=FFF-2014J`)
  await page.click('a:has-text("(2014J)")')
  await page.waitForLoadState('networkidle')
  await skipTour(page)
  await page.locator('.secondary-navigation a:has-text("More")').first().click()
  await page.waitForTimeout(300)
  await page.screenshot({ path: `${OUT}/m01-course-nav.png` })
  await page.locator('.secondary-navigation a:has-text("At-risk insights")').first().click()
  await page.waitForSelector('.xai-table')
  await skipTour(page)
  await page.locator('.xai-table a:has-text("Explain")').nth(12).click()
  await page.waitForSelector('.xai-trail li', { timeout: 60000 })
  const close = page.locator('#theme_boost-drawers-courseindex [data-action="closedrawer"]').first()
  if (await close.isVisible().catch(() => false)) { await close.click(); await page.waitForTimeout(500) }
  await page.screenshot({ path: `${OUT}/m02-instructor.png`, fullPage: true })
  await ctx.close()
}

// Advisor: caseload page from the site navigation.
{
  const { ctx, page } = await session('advisor')
  await page.goto(`${BASE}/local/xairisk/caseload.php`)
  await page.waitForSelector('.xai-trail li', { timeout: 60000 })
  await page.screenshot({ path: `${OUT}/m03-advisor.png`, fullPage: true })
  await ctx.close()
}

// Administrator (Manager role): institution overview.
{
  const { ctx, page } = await session('manager')
  await page.goto(`${BASE}/local/xairisk/overview.php`)
  await page.waitForSelector('.xai-trail li', { timeout: 60000 })
  await page.screenshot({ path: `${OUT}/m04-administrator.png`, fullPage: true })
  await ctx.close()
}

await browser.close()
