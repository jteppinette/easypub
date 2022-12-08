const { render, html, useState } = htmPreact

function App({ slug, title }) {
  const [secret, setSecret] = useState('')
  const [result, setResult] = useState()
  const [validationError, setValidationError] = useState()
  const [httpError, setHTTPError] = useState()
  const [isLoading, setIsLoading] = useState(false)

  const submitText = isLoading ? 'Updating...' : 'Update'

  const url = `${location.protocol}//${location.host}/`

  function submit(event) {
    event.preventDefault()

    setIsLoading(true)

    const content = document.getElementsByClassName('ql-editor')[0].innerHTML

    fetchjson(`/api/${slug}/update`, 'POST', { content, secret })
      .then(({ data }) => {
        setResult(data)

        setValidationError()
        setHTTPError()
      })
      .catch(({ data, response }) => {
        if (response.status == 422) {
          setValidationError(data)
          setHTTPError()
        } else {
          setHTTPError(response.status)
          setValidationError()
        }

        setResult()
      })
      .then(() => setIsLoading(false))
  }

  return html`
    <div class="container">
      <div class="panel panel-white">
        <form onSubmit=${submit}>
          <label for="title">Title</label>
          <input
            value=${title}
            type="text"
            name="title"
            disabled
            placeholder="My Publication Name"
          />

          <label for="secret">Secret</label>
          <input
            value=""
            onChange=${(e) => setSecret(e.target.value)}
            type="password"
            name="secret"
          />

          ${validationError &&
          html`<${ValidationErrorAlert} ...${validationError} />`}
          ${httpError !== undefined &&
          html`<${HTTPErrorAlert} status=${httpError} />`}
          ${result && html`<${SuccessAlert} ...${result} />`}

          <button disabled=${isLoading} type="submit">${submitText}</button>
        </form>
      </div>
    </div>
  `
}

function app({ slug, title }) {
  render(
    html`<${App} slug=${slug} title=${title} />`,
    document.getElementById('app')
  )
}
