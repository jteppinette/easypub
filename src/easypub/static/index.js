const { render, html, useState, useEffect } = htmPreact

function App() {
  const [title, setTitle] = useState('')
  const [result, setResult] = useState()
  const [validationError, setValidationError] = useState()
  const [httpError, setHTTPError] = useState()
  const [isLoading, setIsLoading] = useState(false)

  const submitText = isLoading ? 'Publishing...' : 'Publish'

  function submit(event) {
    event.preventDefault()

    setIsLoading(true)

    const content = document.getElementsByClassName('ql-editor')[0].innerHTML

    fetchjson('/api/publish', 'POST', { title, content })
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
            onInput=${(e) => setTitle(e.target.value)}
            value=${title}
            type="text"
            name="title"
            placeholder="My Publication Name"
          />

          ${validationError &&
          html`<${ValidationErrorAlert} ...${validationError} />`}
          ${httpError !== undefined &&
          html`<${HTTPErrorAlert} status=${httpError} />`}
          ${result && html`<${SuccessAlert} ...${result} />`}

          <button disabled=${isLoading} type="submit" class="primary">
            ${submitText}
          </button>
        </form>
      </div>
    </div>
  `
}

function app() {
  render(html`<${App} />`, document.getElementById('app'))
}
