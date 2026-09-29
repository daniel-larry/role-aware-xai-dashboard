// Log in to Canvas as the imported instructor and capture the dashboard embedded as an External URL item.
// Usage: npm i playwright && STAFF_PASSWORD=... DASHBOARD_PASSWORD=... OUT=docs/screenshots/canvas node tools/canvas_screenshots.mjs
import { chromium } from 'playwright'

const CANVAS = process.env.CANVAS || 'http://localhost:3000'
const OUT = process.env.OUT || '.'
const COURSE = process.env.COURSE || 'FFF-2014J'
const browser = await chromium.launch({ ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) })
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1000 } })).newPage()

await page.goto(`${CANVAS}/login/canvas`)
await page.fill('#pseudonym_session_unique_id', process.env.CANVAS_USER || 'instructor')
await page.fill('#pseudonym_session_password', process.env.CANVAS_PASSWORD || process.env.STAFF_PASSWORD)
await page.click('button[type=submit], input[type=submit]')
await page.waitForLoadState('networkidle')
// First login: accept the terms of use.
const terms = page.locator('input[name="user[terms_of_use]"]')
if (await terms.isVisible().catch(() => false)) {
  await terms.check()
  await page.click('button:has-text("Submit")')
  await page.waitForLoadState('networkidle')
}
// The 2017 image does not recognise current browsers; hide its warning banner.
const hideBanner = () => page.addStyleTag({ content: '.ic-flash-warning, #flash_message_holder { display: none !important; }' })

// Find the Canvas course by its code, then open its "At-risk insights" module item.
// Cookie-authenticated Canvas API responses start with "while(1);".
const api = async (path) => JSON.parse((await (await page.request.get(CANVAS + path)).text()).replace(/^while\(1\);/, ''))
const mine = await api('/api/v1/courses?per_page=100')
const all = mine.length ? mine : await api(`/api/v1/accounts/1/courses?search_term=${COURSE}`)
const course = all.find((c) => c.course_code === COURSE)
await page.goto(`${CANVAS}/courses/${course.id}/modules`)
await page.waitForSelector('text=At-risk insights dashboard')
await hideBanner()
await page.screenshot({ path: `${OUT}/c01-modules.png` })
await page.locator('a.ig-title', { hasText: 'At-risk insights dashboard' }).first().click()

// The item renders the dashboard in an iframe; sign in inside it and explain one student.
const frame = page.frameLocator('iframe#file_content')
await frame.locator('input[autocomplete=username]').fill('instructor')
await frame.locator('input[type=password]').fill(process.env.DASHBOARD_PASSWORD)
await frame.locator('button.primary').click()
await frame.locator('table tbody tr').nth(12).click()
await frame.locator('.trail li').first().waitFor({ timeout: 60000 })
await page.waitForTimeout(800)
await hideBanner()
await page.screenshot({ path: `${OUT}/c02-embedded-instructor.png`, fullPage: true })

await browser.close()
