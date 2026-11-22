import React, { cloneElement, isValidElement } from 'react';
import { useLanguage } from '../../contexts/LanguageContext';

const LOCALIZED_ATTRIBUTES = ['placeholder', 'title', 'aria-label', 'alt'] as const;

/** Applies dictionary translations to exact English UI text without changing dynamic/user data. */
export const LocalizedTree: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { translateText } = useLanguage();

  const translateNode = (node: React.ReactNode): React.ReactNode => {
    if (typeof node === 'string') return translateText(node);
    if (Array.isArray(node)) return node.map((child, index) => <React.Fragment key={index}>{translateNode(child)}</React.Fragment>);
    if (!isValidElement(node)) return node;

    const nodeProps = node.props as Record<string, unknown>;
    const props: Record<string, unknown> = { ...nodeProps };
    LOCALIZED_ATTRIBUTES.forEach((attribute) => {
      const value = props[attribute];
      if (typeof value === 'string') props[attribute] = translateText(value);
    });
    props.children = translateNode(nodeProps.children as React.ReactNode);
    return cloneElement(node, props);
  };

  return <>{translateNode(children)}</>;
};
