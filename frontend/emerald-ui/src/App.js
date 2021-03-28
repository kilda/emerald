import './App.css';
import React from "react";
import Container from "react-bootstrap/Container";
import Row from "react-bootstrap/Row";
import Col from "react-bootstrap/Col";
import ListGroup from "react-bootstrap/ListGroup";
import Modal from "react-bootstrap/Modal";
import Button from "react-bootstrap/Button";
import Form from "react-bootstrap/Form";


class App extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            isLoaded: false,
            modal: false,
            globalModal: false,
            globalColor: null,
            globalSignal: 'SHUTDOWN',
            globalVersion: '',
            items: {},
            error: null,
            current: {
                service: '',
                color: '',
                signal: '',
                state: '',
                expected_state: '',
            }
        };
    }

    getRealtimeData(e) {
        e = JSON.parse(e);
        let key = e.service + '/' + e.color;
        let items = this.state.items;
        items[key] = e
        this.setState(state => ({
            items: items
        }))

    }

    componentWillUnmount() {
        this.state.sseObj.close()
    }

    componentDidMount() {
        this.getComponents();
        const sse = new EventSource('/stream', {withCredentials: true});
        sse.onmessage = e => this.getRealtimeData(e.data);
        sse.onerror = () => {
            // error log here
            sse.close();
        }
        this.setState({
            sseObj: sse
        });

    }

    showGlobalModal(color) {
        this.setState({
            globalModal: true,
            globalColor: color,
        });
    }

    showModal(current) {
        this.setState({
            modal: true,
            current: current
        });
    }

    closeGlobalModal() {
        this.setState({
            globalModal: false,
            globalColor: null,
            globalSignal: 'SHUTDOWN',
            globalVersion: '',
        });
    }

    closeModal() {
        this.setState({
            modal: false,
            current: {
                service: '',
                color: '',
                signal: '',
                state: '',
                version: '',
                expected_state: ''
            }
        });
        this.getComponents()
    }

    async updateCurrent() {
        if (this.state.current.state === '') {
            this.state.current.state = null;
        }
        fetch('/components',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(this.state.current)
            })
            .then(res => {
                this.closeModal();
                this.getComponents();
            })
    }

    async updateGlobal() {
        fetch('/global',
            {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    color: this.state.globalColor,
                    signal: this.state.globalSignal,
                    version: this.state.globalVersion,
                })
            })
            .then(res => {
                this.closeGlobalModal();
                this.getComponents();
            })
    }


    getComponents() {
        fetch("/components",
            {
                credentials: 'include'
            })
            .then(res => res.json())
            .then(
                (result) => {
                    var item_dict = {};
                    result.forEach(el => item_dict[el.service + '/' + el.color] = el);
                    this.setState({
                        isLoaded: true,
                        items: item_dict
                    });
                },
                (error) => {
                    this.setState({
                        isLoaded: true,
                        error
                    });
                }
            );
    }

    updateToggle(val) {
        let cur = this.state.current
        if (val) {
            cur.signal = "START";
        } else {
            cur.signal = "SHUTDOWN";
        }
        this.setState({current: cur})
    }

    updateGlobalToggle(val) {
        let cur = this.state.globalSignal;
        if (val) {
            cur = "START";
        } else {
            cur = "SHUTDOWN";
        }
        this.setState({globalSignal: cur})
    }

    updateVersion(val) {
        console.log(val);
        let cur = this.state.current
        cur.version = val;
        this.setState({current: cur})
    }

    updateGlobalVersion(val) {
        console.log(val);
        this.setState({globalVersion: val})
    }

    get_color(item) {
        if (item.service === "grpc" || item.service === "northbound") {
            return 'success';
        }
        if (item.state > 0 && item.state === item.expected_state) {
            return 'success';
        }
        if (item.state === null || item.state === 0) {
            return 'danger';
        }
        return 'warning';
    }

    render() {
        const {error, isLoaded, items} = this.state;
        if (error) {
            return <div>Error Loading Components: {error.message}</div>;
        } else if (!isLoaded) {
            return <div>Loading...</div>;
        } else {
            var vals = []
            Object.keys(items).forEach(k => vals.push(items[k]));
            vals.sort(function (a, b) {
                return a.service.localeCompare(b.service);
            });
            return (
                <>
                    <Modal
                        show={this.state.globalModal}
                        onHide={() => this.closeGlobalModal()}
                        dialogClassName="modal-90w"
                        aria-labelledby="example-custom-modal-styling-title"
                    >
                        <Modal.Header>
                            <Modal.Title
                                id="example-custom-modal-styling-title">
                                {this.state.globalColor}
                            </Modal.Title>
                        </Modal.Header>
                        <Modal.Body>
                            <Form>
                                <Form.Group controlId="formVersion">
                                    <Form.Label>Version</Form.Label>
                                    <Form.Control type="text"
                                                  onChange={(e) => this.updateGlobalVersion(e.target.value)}
                                                  value={this.state.globalVersion}/>
                                </Form.Group>

                                <Form.Group controlId="formActive">
                                    <Form.Check type="switch"
                                                label="Activate"
                                                checked={this.state.globalSignal === "START"}
                                                onChange={(e) => this.updateGlobalToggle(e.currentTarget.checked)}/>
                                </Form.Group>
                                <Modal.Footer>
                                    <Button variant="primary"
                                            onClick={() => this.updateGlobal()}>
                                        Update
                                    </Button>
                                    <Button variant="secondary"
                                            onClick={() => this.closeGlobalModal()}>
                                        Cancel
                                    </Button>
                                </Modal.Footer>
                            </Form>
                        </Modal.Body>
                    </Modal>
                    <Modal
                        show={this.state.modal}
                        onHide={() => this.closeModal()}
                        dialogClassName="modal-90w"
                        aria-labelledby="example-custom-modal-styling-title"
                    >
                        <Modal.Header>
                            <Modal.Title
                                id="example-custom-modal-styling-title">
                                {this.state.current.service}/{this.state.current.color}
                            </Modal.Title>
                        </Modal.Header>
                        <Modal.Body>
                            <Form>
                                <Form.Group controlId="formVersion">
                                    <Form.Label>Version</Form.Label>
                                    <Form.Control type="text"
                                                  onChange={(e) => this.updateVersion(e.target.value)}
                                                  value={this.state.current.version}/>
                                </Form.Group>

                                <Form.Group controlId="formState">
                                    <Form.Label>State</Form.Label>
                                    <Form.Control type="text"
                                                  value={this.state.current.state} readonly/>
                                </Form.Group>

                                <Form.Group controlId="formExpectedState">
                                    <Form.Label>Expected State</Form.Label>
                                    <Form.Control type="text"
                                                  value={this.state.current.expected_state} readonly/>
                                </Form.Group>

                                <Form.Group controlId="formActive">
                                    <Form.Check type="switch"
                                                label="Activate"
                                                checked={this.state.current.signal === "START"}
                                                onChange={(e) => this.updateToggle(e.currentTarget.checked)}/>
                                </Form.Group>
                                <Modal.Footer>
                                    <Button variant="primary"
                                            onClick={() => this.updateCurrent()}>
                                        Update
                                    </Button>
                                    <Button variant="secondary"
                                            onClick={() => this.closeModal()}>
                                        Cancel
                                    </Button>
                                </Modal.Footer>
                            </Form>
                        </Modal.Body>
                    </Modal>
                    <Container fluid>
                        <Row>
                            <Col>
                                <ListGroup>
                                    <ListGroup.Item
                                        key="blue" variant="secondary"
                                        action onClick={() => this.showGlobalModal("blue")}>
                                        Blue
                                    </ListGroup.Item>

                                    {vals.filter(item => item.color === "blue")
                                        .map(item => (
                                            <ListGroup.Item
                                                key={item.service + '/' + item.color}
                                                variant={this.get_color(item)}
                                                action
                                                onClick={() => this.showModal(item)}
                                            >
                                                {item.service}/{item.color} {item.version}
                                            </ListGroup.Item>

                                        ))}
                                </ListGroup>
                            </Col>
                            <Col>
                                <ListGroup>
                                    <ListGroup.Item
                                        key="green" variant="secondary"
                                        action onClick={() => this.showGlobalModal("green")}>
                                        Green
                                    </ListGroup.Item>
                                    {vals.filter(item => item.color === "green")
                                        .map(item => (
                                            <ListGroup.Item
                                                key={item.service + '/' + item.color}
                                                variant={this.get_color(item)}
                                                action
                                                onClick={() => this.showModal(item)}
                                            >
                                                {item.service}/{item.color} {item.version}
                                            </ListGroup.Item>
                                        ))}
                                </ListGroup>
                            </Col>
                        </Row>
                        <Row className='mt-3'>
                            <Col>
                                <ListGroup>
                                    {vals.filter(item => item.service === "floodlight")
                                        .map(item => (
                                            <ListGroup.Item
                                                key={item.service + '/' + item.color}
                                                variant={item.state ? 'success' : 'danger'}
                                                action
                                                onClick={() => this.showModal(item)}
                                            >
                                                {item.service}/{item.color} {item.version}
                                            </ListGroup.Item>

                                        ))}
                                </ListGroup>
                            </Col>
                            <Col>
                                <ListGroup>
                                    {vals.filter(item => item.color !== "green" && item.color !== "blue" && item.service !== "floodlight")
                                        .map(item => (
                                            <ListGroup.Item
                                                key={item.service + '/' + item.color}
                                                variant='success'>
                                                {item.service}/{item.color} {item.version}
                                            </ListGroup.Item>
                                        ))}
                                </ListGroup>
                            </Col>
                        </Row>
                    </Container>
                </>);
        }
    }

}

export default App;
