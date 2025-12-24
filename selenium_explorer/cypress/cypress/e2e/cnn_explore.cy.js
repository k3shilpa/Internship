Cypress.on('uncaught:exception', (err, runnable) => {
  return false
})

describe("Generic Menu Explorer", () => {

  const BASE_URL = "https://www.w3schools.com"
  const MAX_LINKS = 10

  it("Clicks first 10 clickable menus safely", () => {

    cy.visit(BASE_URL)

    cy.get("a[href]").then(($links) => {

      const hrefs = [...$links]
        .map(link => link.href)
        .filter(href =>
          href.startsWith("http") &&
          href.includes("w3schools.com")
        )

      const uniqueLinks = [...new Set(hrefs)].slice(0, MAX_LINKS)

      cy.wrap(uniqueLinks).each((link, index) => {
        cy.log(`Visiting (${index + 1}): ${link}`)
        cy.visit(link)
        cy.title().should("not.be.empty")
      })
    })
  })
})
