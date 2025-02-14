import { gql } from '@apollo/client';

export const TEST_QUERY = gql`
    query test {
        test
    }
`;

export const REVERSE = gql`
    mutation reverse($str: String!) {
        reverse(str: $str) {
            string
            madeAt
        }
    }
`;

export const REVERSED_SUBSCRIPTION = gql`
    subscription stringReversed {
        stringReversed {
            string
            madeAt
        }
    }
`;
