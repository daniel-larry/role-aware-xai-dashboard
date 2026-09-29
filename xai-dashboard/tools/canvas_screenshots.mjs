// Log in to Canvas as the imported instructor and capture the dashboard embedded as an External URL item.
// Usage: npm i playwright && STAFF_PASSWORD=... DASHBOARD_PASSWORD=... OUT=docs/screenshots/canvas node tools/canvas_screenshots.mjs
import { chromium } from 'playwright'

const CANVAS = process.env.CANVAS || 'http://localhost:3000'
const OUT = process.env.OUT || '.'
const COURSE = process.env.COURSE || 'FFF-2014J'
const browser = await chromium.launch({ ...(process.env.CHROME ? { executablePath: process.env.CHROME } : {}) })
const page = await (await browser.newContext({ viewport: { width: 1440, height: 1000 } })).newPage()

await page.goto(`${CANVAS}/login/canvas`)
await page.fill('#pseudonym_session_unique_id', 'instructor')
await page.fill('#pseudonym_session_password', process.env.STAFF_PASSWORD)
await page.click('button[type=submit], input[type=submit]')
await page.waitForLoadState('networkidle')

// Find the Canvas course by its SIS id, then open its "At-risk insights" module item.
const res = await page.request.get(`${CANVAS}/api/v1/courses/sis_course_id:${COURSE}`)
const course = await res.json()
await page.goto(`${CANVAS}/courses/${course.id}/modules`)
await page.waitForSelector('text=At-risk insights dashboard')
await page.screenshot({ path: `${OUT}/c01-modules.png` })
await page.click('text=At-risk insights dashboard')

// The item renders the dashboard in an iframe; sign in inside it and explain one student.
const frame = page.frameLocator('iframe').first()
await frame.locator('input[autocomplete=username]').fill('instructor')
await frame.locator('input[type=password]').fill(process.env.DASHBOARD_PASSWORD)
await frame.locator('button.primary').click()
await frame.locator('table tbody tr').nth(12).click()
await frame.locator('.trail li').first().waitFor({ timeout: 60000 })
await page.waitForTimeout(800)
await page.screenshot({ path: `${OUT}/c02-embedded-instructor.png`, fullPage: true })

await browser.close()
