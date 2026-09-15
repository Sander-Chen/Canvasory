import React, { useCallback, useEffect, useState } from 'react';
import { Alert, Button, Card, Descriptions, Divider, Select, Space, Spin, Tag, message } from 'antd';
import { CheckCircleOutlined, ThunderboltOutlined } from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { api } from '../api';
import type { Deck, Slide } from '../types';

const IMAGE_5_0_CONFIG_NAME = 'Codex Native Image 5.0 Sol Low Director';

const REFERENCE_INPUT_MAP = [
  {
    input: 'Deck slide content',
    status: 'Required',
    detail: 'The selected deck supplies the ordered slide inputs.',
  },
  {
    input: 'Page 2 seed image',
    status: 'Derived',
    detail: 'The Image 5.0 route seeds the palette from the first content page.',
  },
  {
    input: 'Palette and style context',
    status: 'Forwarded',
    detail: 'The backend route carries bounded seed dependencies to later pages.',
  },
] as const;

const GeneratePage: React.FC = () => {
  const navigate = useNavigate();
  const [decks, setDecks] = useState<Deck[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedDeckId, setSelectedDeckId] = useState<number | null>(null);
  const [slideCount, setSlideCount] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  const [startedBatch, setStartedBatch] = useState<{ batch_id: number; run_ids: number[]; total_runs: number } | null>(null);

  const selectedDeck = decks.find((deck) => deck.id === selectedDeckId);
  const canGenerate = selectedDeckId !== null && slideCount >= 2 && !submitting;

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      setDecks(await api.decks.list());
    } catch (err: unknown) {
      message.error(`Failed to load public generation data: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    queueMicrotask(() => {
      void fetchData();
    });
  }, [fetchData]);

  const handleDeckChange = async (deckId: number) => {
    setSelectedDeckId(deckId);
    setSlideCount(0);
    try {
      const slides: Slide[] = await api.decks.getSlides(deckId);
      setSlideCount(slides.length);
    } catch (err: unknown) {
      setSlideCount(0);
      message.error(`Failed to load deck slides: ${err instanceof Error ? err.message : String(err)}`);
    }
  };

  const handleGenerate = async () => {
    if (!canGenerate || selectedDeckId === null) return;
    setSubmitting(true);
    setStartedBatch(null);
    try {
      const payload = { deck_id: selectedDeckId, mode: 'auto' } as const;
      const result = await api.generate.start(payload);
      setStartedBatch({ batch_id: result.batch_id, run_ids: result.run_ids, total_runs: result.total_runs });
      message.success(`Started Image PPT 5.0 batch #${result.batch_id}`);
    } catch (err: unknown) {
      message.error(`Generate failed: ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="generate-page">
      <div className="page-toolbar">
        <div>
          <h2>Generate Image PPT 5.0</h2>
          <p className="toolbar-subtitle">Choose a deck; the fixed Image 5.0 route starts one Auto generation.</p>
        </div>
        <Tag color="gold">Image Route (5.0)</Tag>
      </div>

      <Spin spinning={loading}>
        <div className="generate-step-grid">
          <Card title="Deck" className="generate-options-panel">
            <Select
              aria-label="Select deck"
              placeholder="Select a deck"
              style={{ width: '100%' }}
              value={selectedDeckId ?? undefined}
              onChange={handleDeckChange}
              options={decks.map((deck) => ({ label: deck.title, value: deck.id }))}
            />
            <Alert
              style={{ marginTop: 12 }}
              type={selectedDeckId === null ? 'info' : slideCount >= 2 ? 'success' : 'warning'}
              showIcon
              message={selectedDeckId === null
                ? 'Select a deck to load its slides.'
                : `${slideCount} slide(s) loaded`}
              description={selectedDeckId !== null && slideCount < 2
                ? 'At least two slides are required before generation can start.'
                : undefined}
            />
          </Card>

          <Card title="Image Route (5.0)" className="generate-options-panel">
            <p>This public route is fixed to the Image 5.0 Auto seed flow.</p>
            <Tag color="gold">engine: image</Tag>
            <Tag color="gold">strategy: image_5_0</Tag>
            <Tag color="gold">mode: auto</Tag>
          </Card>

          <Card title="Reference Input Map" className="generate-options-panel">
            <Descriptions column={1} size="small" bordered>
              {REFERENCE_INPUT_MAP.map((item) => (
                <Descriptions.Item key={item.input} label={item.input}>
                  <Space direction="vertical" size={0}>
                    <Tag color={item.status === 'Required' ? 'blue' : 'default'}>{item.status}</Tag>
                    <span>{item.detail}</span>
                  </Space>
                </Descriptions.Item>
              ))}
            </Descriptions>
          </Card>

          <Card title="Fixed 5.0 Combination" className="generate-options-panel">
            <p>The server owns the single validated Image 5.0 combination.</p>
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Config">{IMAGE_5_0_CONFIG_NAME}</Descriptions.Item>
              <Descriptions.Item label="Route">image_5_0</Descriptions.Item>
              <Descriptions.Item label="Director">gpt-5.6-sol · low</Descriptions.Item>
              <Descriptions.Item label="Renderer">gpt-5.6-luna · low</Descriptions.Item>
              <Descriptions.Item label="Palette">gpt-5.6-sol · low</Descriptions.Item>
            </Descriptions>
          </Card>

          <Card title="Confirm & Generate" className="generate-options-panel generate-confirm-panel">
            <Descriptions column={1} size="small">
              <Descriptions.Item label="Deck">{selectedDeck?.title || '-'}</Descriptions.Item>
              <Descriptions.Item label="Slides">{slideCount}</Descriptions.Item>
              <Descriptions.Item label="Route">Image Route (5.0)</Descriptions.Item>
              <Descriptions.Item label="Mode">Full Auto</Descriptions.Item>
              <Descriptions.Item label="Inputs">Deck slides only.</Descriptions.Item>
            </Descriptions>
            <Divider />
            <Button
              type="primary"
              size="large"
              icon={<ThunderboltOutlined />}
              onClick={handleGenerate}
              loading={submitting}
              disabled={!canGenerate}
              aria-label="Generate Image PPT 5.0"
            >
              Generate Image PPT 5.0
            </Button>
            {!canGenerate && (
              <Alert
                style={{ marginTop: 12 }}
                type="warning"
                showIcon
                message="Generation is not ready"
                description={selectedDeckId === null
                  ? 'Select a deck first.'
                  : 'Select a deck with at least two slides.'}
              />
            )}
            {startedBatch && (
              <>
                <Alert
                  style={{ marginTop: 12 }}
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                  message={`Batch #${startedBatch.batch_id} started`}
                  description={`${startedBatch.total_runs} run(s) submitted.`}
                />
                <Space style={{ marginTop: 12 }} wrap>
                  <Button type="primary" onClick={() => navigate(`/history/batch/${startedBatch.batch_id}`)}>
                    Open Batch #{startedBatch.batch_id}
                  </Button>
                  {startedBatch.run_ids.length > 0 && (
                    <Button onClick={() => navigate(`/history/run/${startedBatch.run_ids[0]}`)}>
                      Run Detail
                    </Button>
                  )}
                </Space>
              </>
            )}
          </Card>
        </div>
      </Spin>
    </div>
  );
};

export default GeneratePage;
