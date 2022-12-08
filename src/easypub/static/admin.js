const { render, html, useState } = htmPreact

function App({ slug, title, quill }) {
  const [secret, setSecret] = useState('')
  const [result, setResult] = useState()
  const [validationError, setValidationError] = useState()
  const [httpError, setHTTPError] = useState()
  const [isLoading, setIsLoading] = useState(false)
  const [isDeleting, setIsDeleting] = useState(false)

  const submitText = isLoading ? 'Updating...' : 'Update'
  const deleteText = isDeleting ? 'Deleting...' : 'Delete'

  function submit(event) {
    event.preventDefault()

    setIsLoading(true)

    const content = quill.root.innerHTML

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

  function destroy(event) {
    event.preventDefault()

    if (confirm('Are you sure you want to delete this publication?')) {
      setIsDeleting(true)

      fetchjson(`/api/${slug}/delete`, 'POST', { secret })
        .then(() => {
          location.href = '/'
        })
        .catch(({ data, response }) => {
          if (response.status == 422) {
            setValidationError(data)
            setHTTPError()
          } else {
            setHTTPError(response.status)
            setValidationError()
          }

          setIsDeleting(false)
        })
    }
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
            value=${secret}
            onInput=${(e) => setSecret(e.target.value)}
            type="password"
            name="secret"
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

        <button disabled=${isLoading} onClick=${destroy} class="danger">
          ${deleteText}
        </button>
      </div>
    </div>
  `
}

function app(props) {
  render(html`<${App} ...${props} />`, document.getElementById('app'))
}
